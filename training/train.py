import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error

# ==============================================================================
# CAU HINH
# ==============================================================================
WORK_DIR = r"D:\NCKH\nckh20252026\training"
INPUT_FILE = 'Optimized_Dataset_for_AI.csv'
OUTPUT_MODEL = 'eco_ai_model.pkl'
OUTPUT_ENCODER = 'brand_encoder.pkl'

# ==============================================================================
# CHUONG TRINH CHINH
# ==============================================================================
if __name__ == "__main__":
    # 1. Thiet lap thu muc
    try:
        os.chdir(WORK_DIR)
        print(f"[OK] Working Directory: {WORK_DIR}")
    except FileNotFoundError:
        print(f"[LOI] Khong tim thay thu muc: {WORK_DIR}")
        exit()

    # 2. Doc file dataset da co san
    if not os.path.exists(INPUT_FILE):
        print(f"[LOI] Khong tim thay file '{INPUT_FILE}'")
        print("-> Vui long kiem tra lai ten file hoac chay code tao data truoc.")
        exit()
        
    print(f"... Dang doc du lieu tu: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"[OK] Da tai {len(df)} dong du lieu.")

    # 3. Tien xu ly (Preprocessing)
    print("... Dang chuan bi du lieu training")
    
    # Ma hoa Brand (Dell -> 1, Apple -> 2...)
    le = LabelEncoder()
    # Chuyen ve string de tranh loi neu co so lan trong ten hang
    df['Brand_Encoded'] = le.fit_transform(df['Brand'].astype(str))

    # Chon cac cot Dau vao (Features) va Dau ra (Target)
    features = ['Brand_Encoded', 'Year_Extracted', 'Screen_Size_Extracted', 'Weight_kg', 'Energy_kWh_Year', 'Repair_Score']
    target = 'Eco_Score_Target'

    # Kiem tra xem file csv co du cot khong
    missing_cols = [col for col in features + [target] if col not in df.columns]
    if missing_cols:
        print(f"[LOI] File CSV thieu cac cot sau: {missing_cols}")
        print("-> File dataset cua ban khong dung chuan. Hay tao lai dataset.")
        exit()

    X = df[features]
    y = df[target]

    # Chia tap Train/Test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train Model
    print("... Dang train Random Forest")
    model = RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42)
    model.fit(X_train, y_train)

    # 5. Danh gia
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    print("-" * 30)
    print(f"KET QUA TRAINING:")
    print(f"-> Do chinh xac (R2): {r2:.4f}")
    print(f"-> Sai so trung binh (MAE): {mae:.2f} diem")
    print("-" * 30)

    # 6. Luu Model
    joblib.dump(model, OUTPUT_MODEL)
    joblib.dump(le, OUTPUT_ENCODER)
    print(f"[THANH CONG] Da luu model: {OUTPUT_MODEL}")
    print(f"[THANH CONG] Da luu encoder: {OUTPUT_ENCODER}")