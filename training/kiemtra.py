import os

# Duong dan ban cung cap
TARGET_DIR = r"D:\NCKH\nckh20252026\training"

print("--- BAT DAU KIEM TRA ---")

# 1. Kiem tra thu muc co ton tai khong
if os.path.exists(TARGET_DIR):
    print(f"[OK] Tim thay thu muc: {TARGET_DIR}")
    
    # 2. Liet ke tat ca file dang co trong do
    files_in_folder = os.listdir(TARGET_DIR)
    print(f"\nDanh sach {len(files_in_folder)} file dang co trong thu muc:")
    for f in files_in_folder:
        print(f"  - {f}")
        
    # 3. Kiem tra tung file bat buoc
    required_files = [
        'boavizta-data-us.csv', 
        'ENERGY_STAR_Certified_Computers_V9.0.csv',
        'laptop.csv', 
        'smartphone.csv', 
        'tablet.csv', 
        'du_lieu_thuc_te.csv'
    ]
    
    print("\n>>> Ket qua doi chieu file nguon:")
    missing_count = 0
    for req in required_files:
        if req in files_in_folder:
            print(f"  [CO] {req}")
        else:
            print(f"  [THIEU] {req} <--- QUAN TRONG")
            missing_count += 1
            
    if missing_count > 0:
        print(f"\n[KET LUAN] Ban dang thieu hoac sai ten {missing_count} file.")
        print("Giai phap: Doi ten cac file trong thu muc cho giong y het danh sach [THIEU] o tren.")
    else:
        print("\n[KET LUAN] Day du file! Ban co the chay file training ngay bay gio.")

else:
    print(f"[LOI] May tinh khong tim thay thu muc: {TARGET_DIR}")
    print("Hay kiem tra lai duong dan folder.")

print("--- KET THUC ---")