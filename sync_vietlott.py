import urllib.request
import pandas as pd
import json
import io
import os

# ID File Google Sheet của anh
SHEET_ID = "1nI_WL-NcOsDyWo1GlfgKI38bMcDn55d4nDBxaz9V6vg"
JSON_OUTPUT_PATH = "api_xoso.json"

# Danh sách các Tab tương ứng trên Google Sheets
SHEETS_CONFIG = [
    {"name": "Lotto 535", "type": "Lotto 535"},
    {"name": "Mega 645", "type": "Mega 645"},
    {"name": "Mega 655", "type": "Mega 655"}
]

all_records = []

def parse_bo_so(bo_so_raw):
    """
    Quy tắc đơn giản 100%:
    - Chuỗi dạng: 0105182633|07
    - Cắt cứ 2 ký tự là 1 số: ['01', '05', '18', '26', '33']
    - Phần sau dấu '|' là số phụ: '07'
    """
    if pd.isna(bo_so_raw) or not str(bo_so_raw).strip():
        return [], None
    
    val_str = str(bo_so_raw).strip()
    bonus = None
    main_str = val_str
    
    # Tách số phụ nếu có dấu |
    if '|' in val_str:
        parts = val_str.split('|')
        main_str = parts[0].strip()
        bonus = parts[1].strip().zfill(2)
        
    # Lấy đúng từng cặp 2 ký tự
    numbers = []
    clean_digits = ''.join(filter(str.isdigit, main_str))
    for i in range(0, len(clean_digits), 2):
        pair = clean_digits[i:i+2]
        if len(pair) == 2:
            numbers.append(pair)
            
    return numbers, bonus

print("=== BẮT ĐẦU ĐỒNG BỘ 3 LOẠI XỔ SỐ TỪ GOOGLE SHEETS ===")

for cfg in SHEETS_CONFIG:
    sheet_name = cfg["name"]
    lottery_type = cfg["type"]
    
    # URL export CSV cho từng tab
    encoded_name = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            csv_data = response.read().decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_data))
            
            # Chuẩn hóa tên cột
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Tìm cột Ngày, Kỳ, Bộ số
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
                    
                # Bỏ phần thập phân nếu kỳ bị format kiểu 999.0
                if ky_val.endswith('.0'):
                    ky_val = ky_val[:-2]
                    
                numbers, bonus = parse_bo_so(boso_val)
                
                if numbers:
                    all_records.append({
                        "ky": ky_val,
                        "ngay": ngay_val,
                        "type": lottery_type,
                        "numbers": numbers,
                        "bonusNumber": bonus
                    })
                    count += 1
            print(f"-> Đã tải thành công tab '{sheet_name}': {count} kỳ quay.")
    except Exception as e:
        print(f"Lỗi tải tab '{sheet_name}': {e}")

# Nếu không tải được qua Google Sheets URL (do riêng tư/chưa share), dùng dữ liệu local chuẩn hóa
if not all_records and os.path.exists(JSON_OUTPUT_PATH):
    print("Dùng file local chuẩn hóa...")
    with open(JSON_OUTPUT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        raw_list = data.get("records", []) if isinstance(data, dict) else data
        for r in raw_list:
            raw_boso = "".join(r.get("numbers", []))
            if r.get("bonusNumber"):
                raw_boso += f"|{r.get('bonusNumber')}"
            nums, bonus = parse_bo_so(raw_boso)
            all_records.append({
                "ky": str(r.get("ky", "")),
                "ngay": str(r.get("ngay", "")),
                "type": r.get("type", "Lotto 535"),
                "numbers": nums,
                "bonusNumber": bonus
            })

# Ghi kết quả ra api_xoso.json
with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump({"records": all_records}, f, ensure_ascii=False, indent=2)

print(f"=== HOÀN TẤT! TỔNG CỘNG {len(all_records)} KỲ QUAY CỦA CẢ 3 TAB ĐÃ ĐƯỢC ĐỒNG BỘ ===")
