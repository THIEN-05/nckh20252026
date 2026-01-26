import pandas as pd
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import os
import sys

# --- CẤU HÌNH ---
DATASET_FILE = 'dataset.csv'
MODEL_FILE = 'eco_model_final.pkl'

print(f">>> Reading data from: {DATASET_FILE}...")

# 1. LOAD DATA
try:
    current_folder = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_folder, DATASET_FILE)
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at {file_path}")
        sys.exit()
    df = pd.read_csv(file_path)
    print(f">>> Successfully loaded {len(df)} rows.")
except Exception as e:
    print(f"Error: {e}")
    sys.exit()

# 2. FEATURE ENGINEERING (TẠO ĐẶC TRƯNG THÔNG MINH)
# Dạy AI hiểu bản chất vật lý thay vì học vẹt con số
# Hiệu suất năng lượng: kWh trên mỗi inch màn hình
df['Energy_Efficiency'] = df['Energy_Consumption_kWh'] / df['Screen_Size_Inch']
# Mật độ vật liệu: Kg trên mỗi inch màn hình
df['Material_Density'] = df['Weight_Kg'] / df['Screen_Size_Inch']

# Xử lý lỗi chia cho 0 (nếu có)
df.replace([np.inf, -np.inf], 0, inplace=True)
df.fillna(0, inplace=True)

# 3. CHỌN CÁC CỘT (Input Features)
# Bây giờ chúng ta có 10 cột đặc trưng
feature_cols = [
    'Energy_Consumption_kWh', 
    'Recycled_Percentage', 
    'RoHS_Compliant', 
    'Screen_Size_Inch', 
    'Weight_Kg', 
    'RAM_GB', 
    'Storage_GB', 
    'CPU_Score',
    'Energy_Efficiency', # <--- Cột mới 1
    'Material_Density'   # <--- Cột mới 2
]

X = df[feature_cols]
y = df['Eco_Score']

# 4. CHIA TẬP TRAIN/TEST
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. HUẤN LUYỆN (CHẾ ĐỘ ỔN ĐỊNH - KHÔNG SMOTE)
print(f">>> Training Realistic Smart Model...")
model = RandomForestClassifier(
    n_estimators=300,       # Số lượng cây quyết định
    max_depth=None,         # Để cây phát triển tự nhiên tối đa
    min_samples_leaf=1,     # Học chi tiết nhất có thể
    random_state=42
)
model.fit(X_train, y_train)

# 6. ĐÁNH GIÁ KẾT QUẢ
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print(f"\n>>> FINAL ACCURACY: {acc * 100:.2f}%")
print("-" * 30)
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# 7. LƯU MODEL
output_path = os.path.join(current_folder, MODEL_FILE)
joblib.dump(model, output_path)
print(f"\n>>> DONE! Smart Model saved to: {output_path}")