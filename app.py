import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import io
import numpy as np
import pycountry

# ==========================================
# 1. CÁC HÀM XỬ LÝ LÕI VÀ ĐỒNG BỘ DỮ LIỆU
# ==========================================

def clean_name(name):
    if pd.isna(name) or name is None: return ""
    name = str(name).upper().replace("*", "").replace(",", " ").replace(".", " ")
    name = re.sub(r'\b(MR|MS|MRS)\b', '', name)
    return " ".join(re.sub(r'[^A-Z ]', '', name).split())

def is_same_guest(name1, name2):
    n1, n2 = clean_name(name1), clean_name(name2)
    if n1 == n2 or n1.replace(" ","") == n2.replace(" ",""): return True
    if len(n1) > 8 and len(n2) > 8 and (n1.replace(" ","") in n2.replace(" ","") or n2.replace(" ","") in n1.replace(" ","")): return True
    arr1 = [w for w in n1.split() if len(w) > 2 and w not in ["BIN", "BINTI", "THI", "VAN", "THE"]]
    arr2 = [w for w in n2.split() if len(w) > 2 and w not in ["BIN", "BINTI", "THI", "VAN", "THE"]]
    return sum(1 for w in arr1 if w in arr2) >= 2 or (len(arr1) <= 1 and sum(1 for w in arr1 if w in arr2) >= 1)

def std_gender(g):
    if pd.isna(g) or not g: return ""
    g = str(g).strip().upper()
    if g in ['M', 'NAM', 'MR.', 'MR', 'MALE']: return 'NAM'
    if g in ['F', 'NỮ', 'NU', 'MS', 'MRS.', 'MRS', 'FEMALE', 'MISS']: return 'NỮ'
    return g

def get_iso3(val):
    if not val or pd.isna(val): return ""
    val = str(val).strip().upper()
    
    vn_map = {
        'VIỆT NAM': 'VNM', 'VN': 'VNM', 'ĐÀI LOAN': 'TWN', 'TW': 'TWN', 
        'TRUNG QUỐC': 'CHN', 'CN': 'CHN', 'CH HÀN': 'KOR', 'HÀN QUỐC': 'KOR', 
        'KR': 'KOR', 'NHẬT BẢN': 'JPN', 'JP': 'JPN', 'HOA KỲ': 'USA', 
        'MỸ': 'USA', 'US': 'USA', 'VƯƠNG QUỐC ANH': 'GBR', 'ANH': 'GBR', 
        'GB': 'GBR', 'UK': 'GBR', 'ÚC': 'AUS', 'Ô-XTRÂY-LI-A': 'AUS', 'Ô-XTRÂY': 'AUS',
        'AU': 'AUS', 'HÀ LAN': 'NLD', 'NL': 'NLD', 'PHÁP': 'FRA', 
        'FR': 'FRA', 'FX': 'FRA', 'ĐỨC': 'DEU', 'DE': 'DEU', 'NGA': 'RUS', 
        'RU': 'RUS', 'RQ': 'RUS', 'THÁI LAN': 'THA', 'TH': 'THA', 
        'MALAYSIA': 'MYS', 'MA-LAI-XI-A': 'MYS', 'MA-LAI': 'MYS', 'MY': 'MYS', 
        'SINGAPORE': 'SGP', 'XIN-GA-PO': 'SGP', 'XIN-GA': 'SGP', 'SG': 'SGP', 
        'INDONESIA': 'IDN', 'IN-ĐÔ-NÊ-XI-A': 'IDN', 'IN-ĐÔ-NÊ': 'IDN', 'ID': 'IDN', 
        'PHILIPPINES': 'PHL', 'PH': 'PHL', 'ẤN ĐỘ': 'IND', 'IN': 'IND', 
        'CANADA': 'CAN', 'CA-NA-DA': 'CAN', 'CA': 'CAN', 
        'MEXICO': 'MEX', 'MÊ-XI-CÔ': 'MEX', 'MX': 'MEX', 'NAM PHI': 'ZAF', 
        'ZA': 'ZAF', 'HỒNG KÔNG': 'HKG', 'HK': 'HKG', 'THỔ NHĨ KỲ': 'TUR', 'THỔ NHĨ': 'TUR',
        'TR': 'TUR', 'NA UY': 'NOR', 'VƯƠNG QUỐC NA-UY': 'NOR', 'NO': 'NOR', 'BA LAN': 'POL', 
        'PL': 'POL', 'ARGENTINA': 'ARG', 'ÁC-HEN-TI-NA': 'ARG', 'AC-HEN-TI-NA': 'ARG', 'AR': 'ARG', 
        'BRAZIL': 'BRA', 'BR': 'BRA', 'TÂY BAN NHA': 'ESP', 'ES': 'ESP', 
        'BỒ ĐÀO NHA': 'PRT', 'PT': 'PRT', 'Ý': 'ITA', 'ITALIA': 'ITA', 
        'IT': 'ITA', 'THỤY SĨ': 'CHE', 'CH': 'CHE', 'THỤY ĐIỂN': 'SWE', 
        'SE': 'SWE', 'ĐAN MẠCH': 'DNK', 'DK': 'DNK', 'PHẦN LAN': 'FIN', 
        'FI': 'FIN', 'ÁO': 'AUT', 'AT': 'AUT', 'BỈ': 'BEL', 'BE': 'BEL', 
        'HY LẠP': 'GRC', 'GR': 'GRC', 'IRELAND': 'IRL', 'AI LÊN': 'IRL', 
        'IE': 'IRL', 'NEW ZEALAND': 'NZL', 'NƯU TÂY LAN': 'NZL', 'NZ': 'NZL', 
        'CAMPUCHIA': 'KHM', 'KH': 'KHM', 'LÀO': 'LAO', 'LA': 'LAO', 
        'MYANMAR': 'MMR', 'MM': 'MMR', 'MACAU': 'MAC', 'MA CAO': 'MAC', 
        'MO': 'MAC', 'TRIỀU TIÊN': 'PRK', 'KP': 'PRK', 'CUBA': 'CUB', 
        'CU BA': 'CUB', 'CU': 'CUB', 'COLOMBIA': 'COL', 'CÔ-LÔM-BI-A': 'COL', 
        'CO': 'COL', 'CHILE': 'CHL', 'CHI-LÊ': 'CHL', 'CL': 'CHL', 
        'PERU': 'PER', 'PE': 'PER', 'AI CẬP': 'EGY', 'EG': 'EGY', 
        'UAE': 'ARE', 'CÁC TIỂU VƯƠNG QUỐC': 'ARE', 'AE': 'ARE', 
        'Ả RẬP XÊ ÚT': 'SAU', 'SA': 'SAU', 'QATAR': 'QAT', 'QA': 'QAT', 
        'ISRAEL': 'ISR', 'IL': 'ISR', 'UKRAINE': 'UKR', 'U-CRAI-NA': 'UKR', 
        'UA': 'UKR', 'BANGLADESH': 'BGD', 'BĂNG-LA-ĐÉT': 'BGD', 'BD': 'BGD', 
        'NEPAL': 'NPL', 'NÊ-PAN': 'NPL', 'NP': 'NPL', 'SRI LANKA': 'LKA', 
        'LK': 'LKA', 'PAKISTAN': 'PAK', 'PA-KÍT-XTAN': 'PAK', 'PK': 'PAK', 
        'MÔNG CỔ': 'MNG', 'MN': 'MNG', 'KAZAKHSTAN': 'KAZ', 'KZ': 'KAZ', 
        'UZBEKISTAN': 'UZB', 'UZ': 'UZB', 'NIGERIA': 'NGA', 'NI-GIÊ-RI-A': 'NGA', 
        'NG': 'NGA', 'MARỐC': 'MAR', 'MA-RỐC': 'MAR', 'MA': 'MAR', 
        'ALGERIA': 'DZA', 'AN-GIÊ-RI': 'DZA', 'DZ': 'DZA', 'KENYA': 'KEN', 
        'KE': 'KEN', 'TANZANIA': 'TZA', 'TZ': 'TZA', 'GHANA': 'GHA', 
        'GH': 'GHA', 'ZAIRE': 'COD', 'ZR': 'COD'
    }
    
    if val in vn_map: return vn_map[val]
    for vn_name, iso3 in vn_map.items():
        if vn_name in val: return iso3
        
    try: return pycountry.countries.lookup(val).alpha_3
    except LookupError: return val

def match_nationality(nat1, nat2):
    if not nat1 or not nat2: return False
    n1, n2 = str(nat1).strip().upper(), str(nat2).strip().upper()
    if n1 == n2: return True
    
    iso1 = get_iso3(n1)
    iso2 = get_iso3(n2)
    
    if iso1 == iso2: return True
    
    # LUẬT NGOẠI LỆ: KBLT khai báo Hồng Kông (HKG) hoặc Ma Cao (MAC) là Trung Quốc (CHN)
    if {iso1, iso2}.issubset({'CHN', 'HKG'}) or {iso1, iso2}.issubset({'CHN', 'MAC'}):
        return True
        
    return False

def parse_date(val, is_dob=False, is_opera=False):
    if pd.isna(val) or val is None or str(val).strip() == "": return None
    if isinstance(val, datetime): return val.replace(tzinfo=None)
    if hasattr(val, 'to_pydatetime'):
        try: return val.to_pydatetime().replace(tzinfo=None)
        except: pass
    
    val_str = str(val).strip()
    if is_opera:
        try: return datetime.strptime(val_str, '%d-%b-%y').replace(tzinfo=None)
        except:
            try: return datetime.strptime(val_str, '%d-%b-%Y').replace(tzinfo=None)
            except: pass
    
    match = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b', val_str)
    if match:
        d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if y < 100: y += 1900 if (is_dob and y > 26) else 2000
        try: return datetime(y, m, d)
        except: return None
    return None

def format_date_vn(dt):
    if pd.isna(dt) or dt is None: return ""
    if isinstance(dt, str): return dt
    if hasattr(dt, 'strftime'): return dt.strftime('%d/%m/%Y')
    return str(dt)

# ==========================================
# 2. ĐỌC DỮ LIỆU TỪ CÁC FILE (EXCEL / XML)
# ==========================================

def parse_kblt_excel(file):
    try:
        df = pd.read_excel(file, header=9)
        df['Ngày sinh'] = df.get('Ngày sinh', df.get('Năm sinh', '')).apply(lambda x: parse_date(x, is_dob=True))
        df['Giới tính'] = df.get('GT', df.get('Giới tính', '')).apply(std_gender)
        df['Quốc tịch'] = df.get('QT', df.get('Quốc tịch', '')).astype(str).str.upper()
        if 'Thời hạn được phép tạm trú tại Việt Nam' in df.columns:
            df['Thời hạn được phép tạm trú tại Việt Nam'] = df['Thời hạn được phép tạm trú tại Việt Nam'].apply(lambda x: parse_date(x))
        return df
    except Exception as e:
        st.error(f"Lỗi đọc KBLT Excel: {e}")
        return pd.DataFrame()

def parse_xml(file, is_police=False):
    try:
        root = ET.parse(file).getroot()
        data = []
        for nd in root.findall('.//G_C9'):
            if not is_police:
                name, dob, gender, nat, passport, visa, din, dout, room = (
                    nd.find('C12'), nd.find('C15'), nd.find('C69'), nd.find('C24'), 
                    nd.find('C30'), nd.find('C33'), nd.find('C36'), nd.find('C39'), nd.find('C42')
                )
            else:
                name, dob, gender, nat, passport, visa, din, dout, room = (
                    nd.find('C15'), nd.find('C21'), nd.find('C24'), nd.find('C33'), 
                    nd.find('C36'), nd.find('C39'), nd.find('C42'), nd.find('C45'), nd.find('C60')
                )
            
            data.append({
                'Họ tên': str(name.text).replace('*', '').strip() if name is not None else "",
                'Ngày sinh': parse_date(dob.text, is_dob=True) if dob is not None else None,
                'Giới tính': std_gender(gender.text) if gender is not None else "",
                'Quốc tịch': str(nat.text).strip().upper() if nat is not None else "",
                'Số hộ chiếu': str(passport.text).strip().upper() if passport is not None else "",
                'Ngày đến ': parse_date(din.text, is_opera=(not is_police)),
                'Thời gian dự kiến tạm trú tại CSLT': parse_date(dout.text, is_opera=(not is_police)),
                'Thời hạn được phép tạm trú tại Việt Nam': visa.text if visa is not None else "",
                'Số phòng': str(room.text).strip().lstrip('0') if room is not None else ""
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Lỗi đọc XML: {e}")
        return pd.DataFrame()

# ==========================================
# 3. ĐỐI CHIẾU 9 TRƯỜNG DỮ LIỆU
# ==========================================
def process_data(check_date, files_dict):
    st.info("Đang tiến hành soi chiếu 9 trường dữ liệu...")
    dfs = {k: (parse_xml(v, is_police=('pol_' in k)) if v.name.endswith('.xml') else parse_kblt_excel(v)) if v else pd.DataFrame() for k, v in files_dict.items()}
            
    all_guests = []
    def extract_info(df, source_label):
        records = []
        if not df.empty:
            for _, r in df.iterrows():
                room = str(r.get('Số phòng', '')).strip().split('.')[0]
                name = str(r.get('Họ tên', '')).strip()
                passp = str(r.get('Số hộ chiếu', '')).strip().upper()
                if not passp or passp == 'NAN': passp = f"NOPASS_{room}_{name[:5]}"
                
                din, dout = r.get('Ngày đến '), r.get('Thời gian dự kiến tạm trú tại CSLT')
                if 'kblt' in source_label: din, dout = parse_date(din), parse_date(dout)
                
                records.append({
                    'Key': passp, 'Room': room, 'Name': name, 
                    'DOB': r.get('Ngày sinh'), 'Gender': r.get('Giới tính', ''), 'Nat': r.get('Quốc tịch', ''),
                    'In': din, 'Out': dout, 'Visa': str(r.get('Thời hạn được phép tạm trú tại Việt Nam', '')).strip(), 
                    'Src': source_label
                })
        return records

    for k in dfs.keys(): all_guests.extend(extract_info(dfs[k], k))

    master_dict = {}
    for g in all_guests:
        found_key = next((k for k, v in master_dict.items() if v['Room'] == g['Room'] and is_same_guest(v['Name'], g['Name'])), g['Key']) if g['Key'] not in master_dict else g['Key']
        if found_key not in master_dict: master_dict[found_key] = {'Room': g['Room'], 'Name': g['Name'], 'Key': g['Key'], 'Srcs': {}}
        master_dict[found_key]['Srcs'][g['Src']] = g

    has_chieu = not dfs['kblt_chieu'].empty or not dfs['gihf_chieu'].empty
    rep_loi, rep_stay, rep_due = [], [], []
    check_dt = datetime.combine(check_date, datetime.min.time())

    for key, data in master_dict.items():
        srcs = data['Srcs']
        in_ks, in_gs, in_ps = 'kblt_sang' in srcs, 'gihf_sang' in srcs, 'pol_sang' in srcs
        in_kc, in_gc, in_pc = 'kblt_chieu' in srcs, 'gihf_chieu' in srcs, 'pol_chieu' in srcs
        
        base_src = next((srcs[s] for s in ['kblt_chieu', 'gihf_chieu', 'kblt_sang', 'gihf_sang', 'pol_chieu', 'pol_sang'] if s in srcs), None)
        if not base_src: continue

        pRoom, pName, pPass = data['Room'], base_src['Name'], base_src['Key']
        pIn, pOut, pVisa = base_src['In'], base_src['Out'], base_src['Visa']
        pDOB, pGender, pNat = base_src['DOB'], base_src['Gender'], base_src['Nat']
        
        out_s = srcs['kblt_sang']['Out'] if in_ks and pd.notna(srcs['kblt_sang'].get('Out')) else (srcs['gihf_sang']['Out'] if in_gs and pd.notna(srcs['gihf_sang'].get('Out')) else None)
        out_c = srcs['kblt_chieu']['Out'] if in_kc and pd.notna(srcs['kblt_chieu'].get('Out')) else (srcs['gihf_chieu']['Out'] if in_gc and pd.notna(srcs['gihf_chieu'].get('Out')) else None)
        
        is_due, is_stay, note, err, loai_loi = False, False, "", "", ""
        
        if has_chieu:
            if pIn == check_dt or in_pc:
                if (in_kc and out_c == check_dt) or (not in_kc and not in_gc and out_s == check_dt): is_due, note = True, "[Day-use] Khách in/out trong ngày"
                else: is_stay, note = True, "Khách mới Check-in" if not pIn or pIn >= check_dt else "Khách Check-in hôm qua"
            if in_ks or in_gs:
                if out_s == check_dt:
                    if not in_kc and not in_gc: is_due, note = True, "Đã Checked-out hoàn toàn"
                    elif out_c and pd.notna(out_c) and out_c > check_dt: is_stay, note = True, f"[Extend] Gia hạn thêm đến {format_date_vn(out_c)}"
                    else: is_due, note = True, "Chưa Checked-out"
                elif out_s and pd.notna(out_s) and out_s > check_dt:
                    if not in_kc and not in_gc: is_due, note = True, "[Shorten] Trả phòng sớm"
                    else:
                        is_stay = True
                        if out_c and pd.notna(out_c) and out_c > out_s: note = f"[Extend] Gia hạn thêm đến {format_date_vn(out_c)}"
                        elif out_c and pd.notna(out_c) and out_c < out_s and out_c == check_dt: is_stay, is_due, note = False, True, "[Shorten] Trả phòng sớm"
            if not any([in_ks, in_gs, in_ps, in_pc]):
                 if out_c == check_dt: is_due = True 
                 else: is_stay = True
        else:
            if pIn == check_dt or in_ps: is_stay, note = True, "Khách Check-in hôm qua" if pIn and pIn < check_dt else "Khách mới Check-in"
            if in_ks or in_gs:
                if out_s == check_dt: is_due, note = True, "Dự kiến Due Out"
                elif out_s and pd.notna(out_s) and out_s > check_dt: is_stay = True

        visa_dt = parse_date(pVisa)
        is_visa_expired = False
        if visa_dt:
            days_left = (visa_dt - check_dt).days
            if days_left < 0: is_visa_expired, err = True, err + f"Khách đã hết hạn Visa từ {format_date_vn(visa_dt)}; "
            elif days_left <= 7: note += f" | [Visa còn {days_left} ngày]"

        b_dict, c_dict, n_b, n_c = None, None, "", ""
        if has_chieu and in_kc and in_gc: b_dict, c_dict, n_b, n_c = srcs['kblt_chieu'], srcs['gihf_chieu'], "Web", "Opera"
        elif not has_chieu and in_ks and in_gs: b_dict, c_dict, n_b, n_c = srcs['kblt_sang'], srcs['gihf_sang'], "Web", "Opera"
        elif not has_chieu and in_ks and in_ps: b_dict, c_dict, n_b, n_c = srcs['kblt_sang'], srcs['pol_sang'], "Web", "Police"

        if b_dict and c_dict:
            if b_dict.get('Room') != c_dict.get('Room'): err += f"Lệch Phòng ({b_dict.get('Room')} vs {c_dict.get('Room')}); "
            if not is_same_guest(b_dict.get('Name', ''), c_dict.get('Name', '')): err += f"Lệch Tên ({b_dict.get('Name')} vs {c_dict.get('Name')}); "
            if b_dict.get('Key') != c_dict.get('Key') and "NOPASS_" not in b_dict.get('Key'): err += f"Lệch Hộ chiếu ({b_dict.get('Key')} vs {c_dict.get('Key')}); "
            if b_dict.get('DOB') != c_dict.get('DOB') and b_dict.get('DOB') and c_dict.get('DOB'): err += f"Lệch Ngày sinh ({format_date_vn(b_dict.get('DOB'))} vs {format_date_vn(c_dict.get('DOB'))}); "
            if b_dict.get('Gender') != c_dict.get('Gender') and b_dict.get('Gender') and c_dict.get('Gender'): err += f"Lệch Giới tính ({b_dict.get('Gender')} vs {c_dict.get('Gender')}); "
            if not match_nationality(b_dict.get('Nat'), c_dict.get('Nat')) and b_dict.get('Nat') and c_dict.get('Nat'): err += f"Lệch Quốc tịch ({b_dict.get('Nat')} vs {c_dict.get('Nat')}); "
            if b_dict.get('In') != c_dict.get('In') and b_dict.get('In') and c_dict.get('In'): err += f"Lệch Ngày In ({format_date_vn(b_dict.get('In'))} vs {format_date_vn(c_dict.get('In'))}); "
            if b_dict.get('Out') != c_dict.get('Out') and b_dict.get('Out') and c_dict.get('Out'): err += f"Lệch Ngày Out ({format_date_vn(b_dict.get('Out'))} vs {format_date_vn(c_dict.get('Out'))}); "
            v_b, v_c = parse_date(b_dict.get('Visa')), parse_date(c_dict.get('Visa'))
            if v_b != v_c and v_b and v_c: err += f"Lệch Hạn Visa ({format_date_vn(v_b)} vs {format_date_vn(v_c)}); "

        if 'NOPASS_' in pPass: loai_loi, err = "Thiếu Passport", "Chưa nhập số Passport; "
        if not pRoom or pRoom == "0" or pRoom.upper() == "PM": loai_loi, err = "Trống Số Phòng", err + "Chưa gán phòng; "

        if is_visa_expired: loai_loi = "Visa Hết Hạn"
        elif err: loai_loi = "Lưu ý"
        else:
            has_sang = not dfs['kblt_sang'].empty or not dfs['gihf_sang'].empty
            if has_chieu:
                if (in_gc or in_pc) and not in_kc: loai_loi = "Thiếu KBLT (Chiều)"
                elif in_kc and not in_gc: loai_loi = "Thiếu Opera (Chiều)"
            elif has_sang:
                if (in_gs or in_ps) and not in_ks: loai_loi = "Thiếu KBLT (Sáng)"
                elif in_ks and not in_gs: loai_loi = "Thiếu Opera (Sáng)"

        if note.startswith(" | "): note = note[3:]

        row_data = {
            'Phân Loại': loai_loi if loai_loi else "",
            'Phòng': pRoom, 'Tên Khách': pName.upper(), 'Passport': pPass if 'NOPASS_' not in pPass else "",
            'Ngày sinh': format_date_vn(pDOB), 'Giới tính': pGender, 'Quốc tịch': pNat,
            'Ngày In': format_date_vn(pIn), 'Ngày Out': format_date_vn(pOut),
            'Hạn Visa': format_date_vn(visa_dt) if visa_dt else "",
            'Trạng Thái/Ghi Chú': note.strip(), 'Chi Tiết': err, 'Hồ Sơ': ""
        }

        if loai_loi: rep_loi.append(row_data)
        if is_due: rep_due.append(row_data)
        elif is_stay: rep_stay.append(row_data)

    return pd.DataFrame(rep_loi), pd.DataFrame(rep_stay), pd.DataFrame(rep_due)

def sort_rooms(df):
    if df.empty: return df
    df['Room_Num'] = df['Phòng'].astype(str).str.extract(r'(\d+)').astype(float)
    df = df.sort_values(by=['Room_Num', 'Phòng'])
    return df.drop(columns=['Room_Num'])

# ==========================================
# 3. GIAO DIỆN STREAMLIT (UI)
# ==========================================
st.set_page_config(page_title="Tool Check IMMI", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>PULLMAN VŨNG TÀU - ĐỐI CHIẾU IMMI</h1>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("☀️ CA SÁNG")
    check_date = st.date_input("Ngày kiểm tra:", format="DD/MM/YYYY")
    fk_s = st.file_uploader("KBLT Sáng (.xls/.xlsx)", type=['xls', 'xlsx'])
    fg_s = st.file_uploader("GIHF Sáng (.xml)", type=['xml'])
    fp_s = st.file_uploader("Police Sáng (.xml)", type=['xml'])
with col2:
    st.subheader("🌙 CA CHIỀU")
    st.write("<br>", unsafe_allow_html=True)
    fk_c = st.file_uploader("KBLT Chiều (.xls/.xlsx)", type=['xls', 'xlsx'])
    fg_c = st.file_uploader("GIHF Chiều (.xml)", type=['xml'])
    fp_c = st.file_uploader("Police Chiều (.xml)", type=['xml'])

st.markdown("---")

if st.button("🚀 CHẠY KIỂM TRA ĐỐI CHIẾU", use_container_width=True):
    files = {'kblt_sang': fk_s, 'gihf_sang': fg_s, 'pol_sang': fp_s, 'kblt_chieu': fk_c, 'gihf_chieu': fg_c, 'pol_chieu': fp_c}
    
    if not any([fk_s, fk_c]):
        st.error("Vui lòng nạp ít nhất 1 file KBLT (Sáng hoặc Chiều) để đối chiếu!")
    else:
        df_loi, df_stay, df_due = process_data(check_date, files)
        cols = ['Phòng', 'Tên Khách', 'Passport', 'Ngày sinh', 'Giới tính', 'Quốc tịch', 'Ngày In', 'Ngày Out', 'Hạn Visa']
        
        df_loi = sort_rooms(df_loi)[['Phân Loại'] + cols + ['Chi Tiết', 'Hồ Sơ']] if not df_loi.empty else df_loi
        df_stay = sort_rooms(df_stay)[cols + ['Trạng Thái/Ghi Chú', 'Hồ Sơ']] if not df_stay.empty else df_stay
        df_due = sort_rooms(df_due)[cols + ['Trạng Thái/Ghi Chú', 'Hồ Sơ']] if not df_due.empty else df_due

        tab1, tab2, tab3 = st.tabs(["📌 Lưu Ý", "🛏️ Stayover", "🚪 Due Out"])
        with tab1: st.dataframe(df_loi, use_container_width=True)
        with tab2: st.dataframe(df_stay, use_container_width=True)
        with tab3: st.dataframe(df_due, use_container_width=True)
            
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_loi.to_excel(writer, sheet_name='Luu_Y', index=False)
            df_stay.to_excel(writer, sheet_name='Stayover', index=False)
            df_due.to_excel(writer, sheet_name='Due Out', index=False)
        
        st.download_button(
            label="📥 Tải Báo Cáo Excel",
            data=buffer.getvalue(),
            file_name=f"Bao_Cao_IMMI_{check_date.strftime('%d%m%Y')}.xlsx",
            mime="application/vnd.ms-excel"
        )