import pandas as pd
import re
import os
import sys

current_folder = os.path.dirname(os.path.abspath(__file__))
FILE_BOA = os.path.join(current_folder, "du_lieu_huan_luyen.csv")
FILE_EPEAT = os.path.join(current_folder, "du_lieu_thuc_te.csv")

print(f">>> Processing in: {current_folder}")

try:
    if not os.path.exists(FILE_BOA) or not os.path.exists(FILE_EPEAT):
        print("ERROR: CSV files not found.")
        sys.exit()
    df_boa = pd.read_csv(FILE_BOA)
    df_epeat = pd.read_csv(FILE_EPEAT)
    print(">>> Files read successfully!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit()

def normalize_name(name):
    if not isinstance(name, str): return str(name)
    name = name.lower()
    for word in ['notebook', 'laptop', 'desktop', 'workstation', 'inc.', 'corp.', 'ltd', 'fusion']:
        name = name.replace(word, '')
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

df_boa['match_key'] = df_boa['name'].apply(normalize_name)
df_epeat['match_key'] = df_epeat['Device Name'].apply(normalize_name)

print(">>> Merging data...")
df_merged = pd.merge(df_boa, df_epeat, on='match_key', how='outer', suffixes=('_BOA', '_EPEAT'))

def clean_ram(value):
    if pd.isna(value): return 8.0
    str_val = str(value).upper().strip()
    try:
        float_val = float(value)
        if 1 <= float_val <= 512: 
            return float_val
    except:
        pass
    match_gb = re.search(r'(\d+(\.\d+)?)\s*GB', str_val)
    if match_gb: return float(match_gb.group(1))
    match_mb = re.search(r'(\d+(\.\d+)?)\s*MB', str_val)
    if match_mb: return float(match_mb.group(1)) / 1024
    match_num = re.search(r'^(\d+(\.\d+)?)$', str_val)
    if match_num:
        val = float(match_num.group(1))
        if 1 <= val <= 512: return val
    return 8.0

def get_cpu_score(row):
    full_text = str(row.get('name', '')) + " " + str(row.get('Device Name', '')) + " " + str(row.get('comment', ''))
    full_text = full_text.upper()
    if any(x in full_text for x in ['M1', 'M2', 'M3', 'APPLE SILICON', 'ARM', 'SNAPDRAGON']): return 1
    if any(x in full_text for x in ['CORE I9', 'RYZEN 9', 'RTX', 'GTX', 'GAMING', 'WORKSTATION']): return 3
    return 2

def clean_storage(value):
    if pd.isna(value): return 256.0
    value = str(value).upper()
    if 'TB' in value: 
        match = re.search(r'(\d+)\s*T', value)
        if match: return float(match.group(1)) * 1024
    match = re.search(r'(\d+)\s*G', value)
    if match: return float(match.group(1))
    return 256.0

def clean_screen(value):
    if pd.isna(value): return 14.0
    match = re.search(r'(\d+(\.\d+)?)', str(value))
    if match: 
        size = float(match.group(1))
        if 10 <= size <= 40: return size
    return 14.0

def clean_weight(value):
    if pd.isna(value): return 1.5
    match = re.search(r'(\d+(\.\d+)?)', str(value))
    if match: return float(match.group(1))
    return 1.5

print(">>> Extracting specs (Updated RAM logic)...")
df_merged['CPU_Score'] = df_merged.apply(get_cpu_score, axis=1)
df_merged['RAM_GB'] = df_merged['memory'].apply(clean_ram)
df_merged['Storage_GB'] = df_merged['hard_drive'].apply(clean_storage)
df_merged['Screen_Size_Inch'] = df_merged['screen_size'].apply(clean_screen)
df_merged['Weight_Kg'] = df_merged['weight'].apply(clean_weight)

df_merged['Final_Name'] = df_merged['Device Name'].fillna(df_merged['name'])

def calculate_score(row):
    if pd.notna(row.get('EPEAT Rank')) and row.get('EPEAT Rank') != 0: return row['EPEAT Rank']
    gwp = row.get('gwp_total')
    if pd.notna(gwp):
        if gwp < 150: return 3
        elif gwp < 250: return 2
        else: return 1
    return 1

df_merged['Eco_Score'] = df_merged.apply(calculate_score, axis=1)

median_energy = df_merged['yearly_tec'].median()
df_merged['Energy_Consumption_kWh'] = df_merged['yearly_tec'].fillna(median_energy)

if 'Recycled %' in df_merged.columns:
    df_merged['Recycled_Percentage'] = df_merged['Recycled %'].fillna(0)
else:
    df_merged['Recycled_Percentage'] = 0

if 'RoHS' in df_merged.columns:
    df_merged['RoHS_Compliant'] = df_merged['RoHS'].fillna(1)
else:
    df_merged['RoHS_Compliant'] = 1

final_cols = [
    'Final_Name', 'Energy_Consumption_kWh', 'Recycled_Percentage', 'RoHS_Compliant',
    'Screen_Size_Inch', 'Weight_Kg', 'RAM_GB', 'Storage_GB', 'CPU_Score', 'Eco_Score'
]
df_final = df_merged[final_cols].rename(columns={'Final_Name': 'Device_Name'})

output_file = os.path.join(current_folder, "FULL_SPECS_CPU_DATASET.csv")
df_final.to_csv(output_file, index=False)

print(f"\n>>> DONE! File saved: {output_file}")

print("\n--- RAM DISTRIBUTION CHECK ---")
print(df_final['RAM_GB'].value_counts())