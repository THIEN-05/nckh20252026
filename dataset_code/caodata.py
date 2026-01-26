import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ---
INPUT_FILE = "epeat.xlsx"  # Tên file Excel của bạn
# Dựa trên ảnh của bạn, tên cột chính xác (có thể phân biệt hoa thường)
COL_LINK = "Product Url"      # Cột G
COL_NAME = "Product Name"     # Cột B
COL_RANK = "EPEAT Tier"       # Cột K

def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Bo comment neu muon chay an
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_from_excel():
    # 1. Đọc file Excel đầu vào
    print(">>> [1] Dang doc file Excel...")
    try:
        # Đọc file Excel
        df = pd.read_excel(INPUT_FILE)
        print(f"-> Da tim thay {len(df)} dong du lieu.")
        
        # Kiểm tra xem tên cột có đúng không
        print("Cac cot tim thay:", list(df.columns))
        
        # Lọc lấy các cột cần thiết (dựa trên tên cột trong ảnh bạn gửi)
        # Nếu tên cột trong Excel khác code, bạn hãy sửa lại biến COL_... ở trên
        if COL_LINK not in df.columns:
            print(f"LOI: Khong tim thay cot '{COL_LINK}'. Hay kiem tra lai file Excel.")
            return
            
    except Exception as e:
        print(f"LOI: Khong doc duoc file '{INPUT_FILE}'. Hay kiem tra ten file.")
        print(e)
        return

    driver = setup_driver()
    detailed_data = []

    # Chạy thử 50 dòng đầu tiên để test (Xóa dòng này nếu muốn chạy hết)
    limit = 50 
    
    print(f">>> [2] Bat dau cao chi tiet {limit} may...")

    # 2. Duyệt qua từng dòng trong Excel
    count = 0
    for index, row in df.iterrows():
        if count >= limit: break
        
        try:
            url = str(row[COL_LINK])
            model_name = str(row[COL_NAME])
            rank_text = str(row[COL_RANK]) # Lay nhan EPEAT co san
            
            # Bỏ qua nếu không phải link hợp lệ
            if "http" not in url: continue
            
            count += 1
            print(f"[{count}] Dang xu ly: {model_name}...")

            driver.get(url)
            time.sleep(3) # Doi trang web tai

            # Click mo rong cac tab thong so (Expansion Panels)
            try:
                driver.execute_script("document.querySelectorAll('.expansion-panel-header').forEach(b => b.click())")
                time.sleep(1)
            except: 
                pass

            # Lay toan bo noi dung text tren web (chuyen ve chu thuong)
            body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            
            # --- TRICH XUAT THONG SO (Logic Regex) ---
            
            # 1. Energy Star
            energy_star = 1 if "energy star" in body_text else 0
            
            # 2. RoHS
            rohs = 1 if "rohs" in body_text or "substance" in body_text else 1
            
            # 3. % Nhua tai che (Recycled Plastic)
            recycled_pct = 0
            # Tìm mẫu câu: "30% post-consumer" hoặc "30% recycled"
            match = re.search(r'(\d{1,3})%\s*(post-consumer|recycled|pcr)', body_text)
            if match:
                try:
                    recycled_pct = int(match.group(1))
                except: pass
            
            # 4. De thao lap (Disassembly)
            easy_fix = 1 if "disassembly" in body_text or "modular" in body_text else 0

            # 5. Chuan hoa EPEAT Rank sang so (Label)
            rank_score = 1 # Mac dinh la Bronze
            rank_lower = rank_text.lower()
            if "gold" in rank_lower: rank_score = 3
            elif "silver" in rank_lower: rank_score = 2
            
            detailed_data.append({
                "Device Name": model_name,
                "Energy Star": energy_star,
                "RoHS": rohs,
                "Recycled %": recycled_pct,
                "Easy Disassemble": easy_fix,
                "EPEAT Rank": rank_score
            })
            
        except Exception as e:
            print(f"-> Loi khi cao link nay: {e}")
            continue

    driver.quit()

    # 3. Luu ket qua
    if detailed_data:
        output_df = pd.DataFrame(detailed_data)
        output_df.to_csv("du_lieu_huan_luyen.csv", index=False, encoding='utf-8-sig')
        print(f"\n>>> [XONG] Da luu {len(output_df)} dong vao 'du_lieu_huan_luyen.csv'")
    else:
        print("Khong lay duoc du lieu nao.")

if __name__ == "__main__":
    scrape_from_excel()