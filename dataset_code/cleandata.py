import pandas as pd
import numpy as np
import re
import os

# --- 1. CONFIGURATION ---
FOLDER_PATH = r"D:\NCKH\nckh20252026\dataset_code"
try:
    os.chdir(FOLDER_PATH)
    print(f"[OK] Working directory changed to: {os.getcwd()}")
except FileNotFoundError:
    print(f"[ERROR] Directory not found: {FOLDER_PATH}")
    print("-> Please check the FOLDER_PATH variable.")
    exit()

# --- 2. HELPER FUNCTIONS ---
def normalize_model_name(name):
    """Normalize model name for matching."""
    if pd.isna(name): return ""
    name = str(name).lower()
    remove_words = ['notebook', 'laptop', 'smartphone', 'tablet', 'mobile', 'inch', 'gb', 'tb', 'wifi', '5g', '4g', 'series']
    for word in remove_words:
        name = name.replace(word, '')
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def extract_features(row):
    """Extract Year and Screen Size from Model Name."""
    name = str(row['Model_Original']).lower()
    
    # Extract Year (e.g., 2021)
    year_match = re.search(r'20(1[0-9]|2[0-5])', name)
    year = int(year_match.group(0)) if year_match else np.nan
    
    # Extract Screen Size (e.g., 14 inch)
    screen_match = re.search(r'(\d{2}(\.\d)?)\s?inch', name)
    screen = float(screen_match.group(1)) if screen_match else np.nan
    
    return pd.Series([year, screen])

# --- 3. LOAD & MERGE DATA ---
print("... Loading and merging data files")
try:
    # Load raw CSVs
    df_boa = pd.read_csv('boavizta-data-us.csv')
    df_energy = pd.read_csv('ENERGY_STAR_Certified_Computers_V9.0.csv')
    df_laptop = pd.read_csv('laptop.csv')
    df_phone = pd.read_csv('smartphone.csv')
    df_tablet = pd.read_csv('tablet.csv')
    df_real = pd.read_csv('du_lieu_thuc_te.csv')

    # Prepare Boavizta (Master Table)
    df_boa = df_boa[df_boa['category'].isin(['Workplace', 'Smartphone', 'Tablet', 'Laptop'])]
    df_boa = df_boa[['manufacturer', 'name', 'category', 'gwp_total', 'weight', 'lifetime']]
    df_boa.columns = ['Brand', 'Model_Original', 'Category', 'Carbon_Footprint', 'Weight_kg', 'Lifetime_Years']
    df_boa['Match_Key'] = df_boa['Model_Original'].apply(normalize_model_name)

    # Prepare Energy Star
    tec_col = [c for c in df_energy.columns if 'TEC' in c and 'kWh' in c]
    if tec_col:
        df_energy = df_energy[['Brand Name', 'Model Name', tec_col[0]]]
        df_energy.columns = ['Brand_En', 'Model_En', 'Energy_kWh_Year']
    else:
        df_energy = df_energy[['Brand Name', 'Model Name']]
        df_energy['Energy_kWh_Year'] = np.nan
        print("[WARN] TEC column not found in Energy Star file.")
        
    df_energy['Match_Key'] = df_energy['Model_En'].apply(normalize_model_name)
    df_energy_agg = df_energy.groupby('Match_Key').agg({'Energy_kWh_Year': 'mean'}).reset_index()

    # Prepare iFixit
    df_fix = pd.concat([df_laptop, df_phone, df_tablet])
    df_fix = df_fix[['Manufacturer', 'Model', 'Score']]
    df_fix.columns = ['Brand_Fix', 'Model_Fix', 'Repair_Score']
    df_fix['Match_Key'] = df_fix['Model_Fix'].apply(normalize_model_name)
    df_fix_agg = df_fix.groupby('Match_Key').agg({'Repair_Score': 'mean'}).reset_index()

    # Prepare Real Data
    df_real = df_real[['Device Name', 'RoHS', 'Recycled %']]
    df_real.columns = ['Model_Real', 'RoHS_Compliant', 'Recycled_Content_Percent']
    df_real['Match_Key'] = df_real['Model_Real'].apply(normalize_model_name)

    # MERGE ALL
    df = pd.merge(df_boa, df_energy_agg, on='Match_Key', how='left')
    df = pd.merge(df, df_fix_agg, on='Match_Key', how='left')
    df = pd.merge(df, df_real, on='Match_Key', how='left')

except Exception as e:
    print(f"[ERROR] File processing error: {e}")
    exit()

# --- 4. SMART PROCESSING (CORE LOGIC) ---
print("... Performing Smart Processing & Imputation")

# A. Feature Engineering
df[['Year_Extracted', 'Screen_Size_Extracted']] = df.apply(extract_features, axis=1)

# B. Smart Imputation
# Default Year to 2021, Screen to 14.0 if missing
df['Year_Extracted'] = df['Year_Extracted'].fillna(2021)
df['Screen_Size_Extracted'] = df['Screen_Size_Extracted'].fillna(14.0)

# Fill Weight: Based on Screen Size
df['Weight_kg'] = df['Weight_kg'].fillna(df.groupby('Screen_Size_Extracted')['Weight_kg'].transform('mean'))
df['Weight_kg'] = df['Weight_kg'].fillna(1.5) # Final fallback

# Fill Energy: Based on Year and Screen Size
df['Energy_kWh_Year'] = df['Energy_kWh_Year'].fillna(df.groupby(['Year_Extracted', 'Screen_Size_Extracted'])['Energy_kWh_Year'].transform('mean'))
df['Energy_kWh_Year'] = df['Energy_kWh_Year'].fillna(30.0) # Final fallback

# Fill others
df['Repair_Score'] = df['Repair_Score'].fillna(6.0)
df['RoHS_Compliant'] = df['RoHS_Compliant'].fillna(1)
df['Recycled_Content_Percent'] = df['Recycled_Content_Percent'].fillna(0)

# C. Calculate Target "Ground Truth" (Eco_Score)
def calculate_target(row):
    # Carbon (Standard: 500kg = 0 points)
    co2 = row['Carbon_Footprint'] if not pd.isna(row['Carbon_Footprint']) else 250
    score_co2 = max(0, 100 - (co2 / 5))
    
    # Energy (Standard: 100kWh = 0 points)
    energy = row['Energy_kWh_Year']
    score_energy = max(0, 100 - energy)
    
    # Repair (Scale 10 -> 100)
    score_repair = row['Repair_Score'] * 10
    
    # Material
    score_mat = row['Recycled_Content_Percent'] + (10 if row['RoHS_Compliant'] else 0)
    score_mat = min(100, score_mat)
    
    # Weighted Formula
    return (0.4 * score_co2) + (0.3 * score_energy) + (0.2 * score_repair) + (0.1 * score_mat)

df['Eco_Score_Target'] = df.apply(calculate_target, axis=1)

# --- 5. SAVE FINAL DATASET ---
train_df = df[[
    'Model_Original',        # For Lookup
    'Brand',                 # Input Feature
    'Year_Extracted',        # Input Feature
    'Screen_Size_Extracted', # Input Feature
    'Weight_kg',             # Input Feature
    'Energy_kWh_Year',       # Input Feature
    'Repair_Score',          # Input Feature
    'Eco_Score_Target'       # TARGET LABEL
]]

output_file = 'Optimized_Dataset_for_AI.csv'
train_df.to_csv(output_file, index=False)

print("="*60)
print(f"[SUCCESS] Dataset created: {os.path.join(FOLDER_PATH, output_file)}")
print("This dataset is ready for training Random Forest.")
print(f"Total rows: {len(train_df)}")
print(train_df.head())
print("="*60)