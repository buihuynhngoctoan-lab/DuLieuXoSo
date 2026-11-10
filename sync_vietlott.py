cat << 'EOF' > /Users/huynhtoan/VietlottSync/sync_vietlott.py
import urllib.request
import pandas as pd
import json
import re
import os

# Đường dẫn file JSON đầu ra
JSON_OUTPUT_PATH = "api_xoso.json"

def clean_number_pair(val):
    """Đưa số về dạng 2 chữ số chuẩn (ví dụ: 1 -> '01', '5' -> '05')"""
    if pd.isna(val) or val == "":
        return None
    val_str = str(val).strip()
    clean_digits = re.sub(r'[^\d]', '', val_str)
    if clean_digits:
        return f"{int(clean_digits):02d}"
    return None

def process_numbers_list(numbers_raw):
    """Tách danh sách các con số thành mảng các cặp 2 chữ số ["01", "02", ...]"""
    if isinstance(numbers_raw, list):
        result = []
        for n in numbers_raw:
            cleaned = clean_number_pair(n)
            if cleaned:
                result.append(cleaned)
        return result
    
    if isinstance(numbers_raw, str):
        # Tách theo dấu phẩy, khoảng trắng, gạch ngang
        parts = re.split(r'[,;\s\-]+', numbers_raw)
        result = [clean_number_pair(p) for p in parts if clean_number_pair(p)]
        if result:
            return result
        # Nếu là chuỗi số dài dính liền (VD: "0102030405")
        clean_str = re.sub(r'[^\d]', '', numbers_raw)
        if len(clean_str) >= 4 and len(clean_str) % 2 == 0:
            return [clean_str[i:i+2] for i in range(0, len(clean_str), 2)]
            
    return []

# Nguồn Google Sheets (Thay URL này bằng URL Google Sheets công khai của anh nếu có)
# Lưu ý: Python sẽ xử lý chuẩn hóa toàn bộ dữ liệu hiện có
all_records = []

# Mẫu cấu trúc dữ liệu chuẩn để kiểm tra
print("Đang xử lý và chuẩn hóa dữ liệu xổ số...")

# Đọc file api_xoso.json cũ nếu có để chuẩn hóa lại
if os.path.exists(JSON_OUTPUT_PATH):
    try:
        with open(JSON_OUTPUT_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            raw_list = data.get("records", []) if isinstance(data, dict) else data
            
            for item in raw_list:
                # Chuẩn hóa Loại xổ số
                raw_type = str(item.get("type", "")).strip()
                norm_type = raw_type
                if "535" in raw_type or "5/35" in raw_type:
                    norm_type = "Lotto 535"
                elif "645" in raw_type or "6/45" in raw_type:
                    norm_type = "Mega 645"
                elif "655" in raw_type or "6/55" in raw_type or "Power" in raw_type:
                    norm_type = "Mega 655"
                
                # Chuẩn hóa Mảng số
                numbers = process_numbers_list(item.get("numbers", []))
                
                # Chuẩn hóa Số Bonus
                bonus = clean_number_pair(item.get("bonusNumber") or item.get("bonus_number") or item.get("bonus"))
                
                record = {
                    "ky": str(item.get("ky", "")).strip(),
                    "ngay": str(item.get("ngay", "")).strip(),
                    "type": norm_type,
                    "numbers": numbers,
                    "bonusNumber": bonus
                }
                all_records.append(record)
    except Exception as e:
        print(f"Lỗi đọc file cũ: {e}")

# Ghi ra file JSON chuẩn cấu trúc
output_data = {"records": all_records}

with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Hoàn tất! Tổng cộng {len(all_records)} bản ghi đã được chuẩn hóa vào {JSON_OUTPUT_PATH}")
EOF

