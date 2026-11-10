import urllib.request
import urllib.parse
import pandas as pd
import json
import io
import os

SHEET_ID = "1nI_WL-NcOsDyWo1GlfgKI38bMcDn55d4nDBxaz9V6vg"
JSON_OUTPUT_PATH = "api_xoso.json"

# Cấu hình độ dài số ký tự kỳ vọng cho phần số chính (chưa tính số phụ)
SHEETS_CONFIG = [
    {"name": "Lotto 535", "type": "Lotto 535", "digits": 10}, # 5 cặp = 10 số
    {"name": "Mega 645", "type": "Mega 645", "digits": 12}, # 6 cặp = 12 số
    {"name": "Mega 655", "type": "Mega 655", "digits": 12}  # 6 cặp = 12 số
]

all_records = []

def parse_bo_so(bo_so_raw, expected_digits):
    if pd.isna(bo_so_raw) or not str(bo_so_raw).strip():
        return [], None
    
    val_str = str(bo_so_raw).strip()
    bonus = None
    main_str = val_str
    
    # 1. Tách số phụ sau dấu | nếu có
    if '|' in val_str:
        parts = val_str.split('|')
        main_str = parts[0].strip()
        bonus = parts[1].strip().zfill(2)
        
    # 2. Lấy toàn bộ chữ số
    clean_digits = ''.join(filter(str.isdigit, main_str))
    
    # 3. BÙ SỐ 0 Ở ĐẦU NẾU BỊ MẤT SỐ 0 (Chống xô lệch cặp số)
    if len(clean_digits) == expected_digits - 1:
        clean_digits = "0" + clean_digits
        
    # 4. Cắt đúng 2 ký tự từ trái qua phải không bỏ sót
    numbers = []
    for i in range(0, len(clean_digits), 2):
        pair = clean_digits[i:i+2]
        if len(pair) == 2:
            numbers.append(pair)
            
    return numbers, bonus

print("=== ĐỒNG BỘ DỮ LIỆU BẢO TOÀN SỐ 0 Ở ĐẦU ===")

for cfg in SHEETS_CONFIG:
    sheet_name = cfg["name"]
    lottery_type = cfg["type"]
    expected_digits = cfg["digits"]
    
    encoded_name = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            csv_data = response.read().decode('utf-8')
            # Đọc CSV dưới dạng STRING 100% để giữ nguyên số 0 ở đầu
            df = pd.read_csv(io.StringIO(csv_data), dtype=str)
            
            df.columns = [str(c).strip().lower() for c in df.columns]
            col_ngay = next((c for c in df.columns if 'ngày' in c or 'ngay' in c), df.columns[0])
            col_ky = next((c for c in df.columns if 'kỳ' in c or 'ky' in c), df.columns[1])
            col_boso = next((c for c in df.columns if 'bộ số' in c or 'bo so' in c or 'bộ' in c), df.columns[2])
            
            count = 0
            for _, row in df.iterrows():
                ky_val = str(row[col_ky]).strip()
                ngay_val = str(row[col_ngay]).strip()
                boso_val = row[col_boso]
                
                if pd.isna(ky_val) or ky_val == "" or ky_val == "nan":
                    continue
                    
                if ky_val.endswith('.0'):
                    ky_val = ky_val[:-2]
                    
                numbers, bonus = parse_bo_so(boso_val, expected_digits)
                
                if numbers:
                    all_records.append({
                        "ky": ky_val,
                        "ngay": ngay_val,
                        "type": lottery_type,
                        "numbers": numbers,
                        "bonusNumber": bonus
                    })
                    count += 1
            print(f"-> Đã xử lý chuẩn xác tab '{sheet_name}': {count} kỳ quay.")
    except Exception as e:
        print(f"Lỗi tải tab '{sheet_name}': {e}")

# Ghi đè file JSON và đẩy lên GitHub
with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump({"records": all_records}, f, ensure_ascii=False, indent=2)

print(f"=== TỔNG CỘNG {len(all_records)} KỲ QUAY ĐÃ ĐƯỢC CHUẨN HÓA SỐ 0 ====")
