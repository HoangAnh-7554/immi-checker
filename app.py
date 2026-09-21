import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import io

# ==========================================
# 1. CÁC HÀM XỬ LÝ LÕI (CORE LOGIC)
# ==========================================

def clean_name(name):
    if pd.isna(name) or name is None: return ""
    name = str(name).upper().replace("*", "").replace(",", " ").replace(".", " ")
    name = re.sub(r'\b(MR|MS|MRS)\b', '', name)
    name = re.sub(r'[^A-Z ]', '', name)
    return " ".join(name.split())

def is_same_guest(name1, name2):
    n1 = clean_name(name1)
    n2 = clean_name(name2)
    if n1 == n2 or n1.replace(" ","") == n2.replace(" ",""): return True
    if len(n1) > 8 and len(n2) > 8:
        if n1.replace(" ","") in n2.replace(" ","") or n2.replace(" ","") in n1.replace(" ",""):
            return True
            
    arr1 = [w for w in n1.split() if len(w) > 2 and w not in ["BIN", "BINTI", "THI", "VAN", "THE"]]
    arr2 = [w for w in n2.split() if len(w) > 2 and w not in ["BIN", "BINTI", "THI", "VAN", "THE"]]
    
    match_count = sum(1 for w in arr1 if w in arr2)
    return match_count >= 2 or (len(arr1) <= 1 and match_count >= 1)

def convert_opera_date(op_date):
    if pd.isna(op_date) or not op_date: return None
    op_date = str(op_date).strip()
    try:
        return datetime.strptime(op_date, '%d-%b-%y')
    except:
        return None

def extract_visa_date(txt):
    if pd.isna(txt) or not txt: return None
    txt = str(txt).strip()
    match = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b', txt)
    if match:
        d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if y < 100: y += 2000
        try:
            return datetime(y, m, d)
        except:
            return None
    return None

def format_date_vn(dt):
    if pd.isna(dt) or dt is None: return ""
    if isinstance(dt, str): return dt
    return dt.strftime('%d/%m/%Y')

def parse_kblt_excel(file):
    try:
        df = pd.read_excel(file, header=9)
        df['Thời hạn được phép tạm trú tại Việt Nam'] = df['Thời hạn được phép tạm trú tại Việt Nam'].apply(
            lambda x: x if extract_visa_date(x) is not None else None
        )
        return df
    except Exception as e:
        st.error(f"Lỗi đọc KBLT Excel: {e}")
        return pd.DataFrame()

def parse_opera_xml(file):
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        data = []
        for nd in root.findall('.//G_C9'):
            name = nd.find('C12').text if nd.find('C12') is not None else (nd.find('C15').text if nd.find('C15') is not None else "")
            passport = nd.find('C30').text if nd.find('C30') is not None else ""
            room = nd.find('C42').text if nd.find('C42') is not None else ""
            date_in_str = nd.find('C36').text if nd.find('C36') is not None else (nd.find('C42').text if nd.find('C42') is not None else "")
            date_out_str = nd.find('C39').text if nd.find('C39') is not None else (nd.find('C45').text if nd.find('C45') is not None else "")
            visa = nd.find('C33').text if nd.find('C33') is not None else ""
            
            data.append({
                'Họ tên': name.replace('*', ''),
                'Số hộ chiếu': passport,
                'Số phòng': str(room).strip().lstrip('0'),
                'Ngày đến ': convert_opera_date(date_in_str),
                'Thời gian dự kiến tạm trú tại CSLT': convert_opera_date(date_out_str),
                'Thời hạn được phép tạm trú tại Việt Nam': visa
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Lỗi đọc Opera/Police XML: {e}")
        return pd.DataFrame()

# ==========================================
# 2. XỬ LÝ SO SÁNH VÀ XUẤT BÁO CÁO
# ==========================================
def process_data(check_date, files_dict):
    st.info("Đang tiến hành đối chiếu dữ liệu...")
    
    dfs = {}
    for key, file in files_dict.items():
        if file is not None:
            if file.name.endswith('.xml'):
                dfs[key] = parse_opera_xml(file)
            else:
                dfs[key] = parse_kblt_excel(file)
        else:
            dfs[key] = pd.DataFrame()
            
    all_guests = []
    
    def extract_info(df, source_label):
        records = []
        if not df.empty:
            for _, row in df.iterrows():
                room = str(row.get('Số phòng', '')).strip().split('.')[0]
                name = str(row.get('Họ tên', '')).strip()
                passp = str(row.get('Số hộ chiếu', '')).strip()
                if not passp or passp == 'nan': passp = f"NOPASS_{room}_{name[:5]}"
                
                din = row.get('Ngày đến ', None)
                if isinstance(din, str): din = extract_visa_date(din)
                dout = row.get('Thời gian dự kiến tạm trú tại CSLT', None)
                if isinstance(dout, str): dout = extract_visa_date(dout)
                
                visa = str(row.get('Thời hạn được phép tạm trú tại Việt Nam', '')).strip()
                
                records.append({
                    'Key': passp, 'Room': room, 'Name': name, 
                    'In': din, 'Out': dout, 'Visa': visa, 'Src': source_label
                })
        return records

    for k in dfs.keys(): 
        all_guests.extend(extract_info(dfs[k], k))

    master_dict = {}
    for g in all_guests:
        found_key = None
        if g['Key'] in master_dict:
            found_key = g['Key']
        else:
            for existing_key, data in master_dict.items():
                if data['Room'] == g['Room'] and is_same_guest(data['Name'], g['Name']):
                    found_key = existing_key
                    break
        
        if found_key is None:
            found_key = g['Key']
            master_dict[found_key] = {
                'Room': g['Room'], 'Name': g['Name'], 'Key': g['Key'],
                'Srcs': {}
            }
        
        master_dict[found_key]['Srcs'][g['Src']] = g

    has_chieu = not dfs['kblt_chieu'].empty or not dfs['gihf_chieu'].empty
    
    rep_loi, rep_stay, rep_due = [], [], []

    for key, data in master_dict.items():
        srcs = data['Srcs']
        in_ks, in_gs, in_ps = 'kblt_sang' in srcs, 'gihf_sang' in srcs, 'pol_sang' in srcs
        in_kc, in_gc, in_pc = 'kblt_chieu' in srcs, 'gihf_chieu' in srcs, 'pol_chieu' in srcs
        
        base_src = None
        for s in ['kblt_chieu', 'gihf_chieu', 'kblt_sang', 'gihf_sang', 'pol_chieu', 'pol_sang']:
            if s in srcs:
                base_src = srcs[s]
                break
        if not base_src: continue

        pRoom, pName, pPass, pIn, pOut, pVisa = data['Room'], base_src['Name'], base_src['Key'], base_src['In'], base_src['Out'], base_src['Visa']
        
        out_s = srcs['kblt_sang']['Out'] if in_ks and srcs['kblt_sang'].get('Out') else (srcs['gihf_sang']['Out'] if in_gs and srcs['gihf_sang'].get('Out') else None)
        out_c = srcs['kblt_chieu']['Out'] if in_kc and srcs['kblt_chieu'].get('Out') else (srcs['gihf_chieu']['Out'] if in_gc and srcs['gihf_chieu'].get('Out') else None)
        
        is_due, is_stay, note, err, loai_loi = False, False, "", "", ""

        check_dt = datetime.combine(check_date, datetime.min.time())
        
        if has_chieu:
            if pIn == check_dt or in_pc:
                if (in_kc and out_c == check_dt) or (not in_kc and not in_gc and out_s == check_dt):
                    is_due, note = True, "[Day-use] Khách in/out trong ngày"
                else:
                    is_stay, note = True, "Khách mới Check-in" if not pIn or pIn >= check_dt else "Khách Check-in hôm qua"
            
            if in_ks or in_gs:
                if out_s == check_dt:
                    if not in_kc and not in_gc:
                        is_due, note = True, "Đã Checked-out hoàn toàn"
                    elif out_c and out_c > check_dt:
                        is_stay, note = True, f"[Extend] Gia hạn thêm đến {format_date_vn(out_c)}"
                    else:
                        is_due, note = True, "Chưa Checked-out"
                elif out_s and out_s > check_dt:
                    if not in_kc and not in_gc:
                        is_due, note = True, "[Shorten] Trả phòng sớm"
                    else:
                        is_stay = True
                        if out_c and out_c > out_s:
                            note = f"[Extend] Gia hạn thêm đến {format_date_vn(out_c)}"
                        elif out_c and out_c < out_s and out_c == check_dt:
                            is_stay, is_due, note = False, True, "[Shorten] Trả phòng sớm"
            
            if not any([in_ks, in_gs, in_ps, in_pc]):
                 if out_c == check_dt: is_due = True 
                 else: is_stay = True
        else:
            if pIn == check_dt or in_ps:
                is_stay, note = True, "Khách Check-in hôm qua" if pIn and pIn < check_dt else "Khách mới Check-in"
            if in_ks or in_gs:
                if out_s == check_dt: is_due, note = True, "Dự kiến Due Out"
                elif out_s and out_s > check_dt: is_stay = True

        visa_dt = extract_visa_date(pVisa)
        if visa_dt:
            days_left = (visa_dt - check_dt).days
            if days_left < 0: note += " | [VISA HẾT HẠN]"
            elif days_left <= 7: note += f" | [Visa còn {days_left} ngày]"

        base_dict, comp_dict, n_base, n_comp = None, None, "", ""
        if has_chieu and in_kc and in_gc:
            base_dict, comp_dict, n_base, n_comp = srcs['kblt_chieu'], srcs['gihf_chieu'], "Web", "Opera"
        elif not has_chieu and in_ks and in_gs:
            base_dict, comp_dict, n_base, n_comp = srcs['kblt_sang'], srcs['gihf_sang'], "Web", "Opera"
        elif not has_chieu and in_ks and in_ps:
            base_dict, comp_dict, n_base, n_comp = srcs['kblt_sang'], srcs['pol_sang'], "Web", "Police"

        if base_dict and comp_dict:
            if base_dict.get('Room') != comp_dict.get('Room'):
                err += f"Lệch Phòng ({n_base}: {base_dict.get('Room')} vs {n_comp}: {comp_dict.get('Room')}); "
            if base_dict.get('Out') != comp_dict.get('Out'):
                err += f"Lệch Ngày Out ({n_base}: {format_date_vn(base_dict.get('Out'))} vs {n_comp}: {format_date_vn(comp_dict.get('Out'))}); "
            if not is_same_guest(base_dict.get('Name', ''), comp_dict.get('Name', '')):
                err += f"Lệch Tên ({n_base}: {base_dict.get('Name')} vs {n_comp}: {comp_dict.get('Name')}); "

        if 'NOPASS_' in pPass: 
            loai_loi, err = "Thiếu Passport", "Chưa nhập số Passport; "
        if not pRoom or pRoom == "0" or pRoom.upper() == "PM": 
            loai_loi, err = "Trống Số Phòng", err + "Chưa gán phòng; "

        if err: loai_loi = loai_loi or "Lệch Dữ Liệu"
        elif has_chieu and in_gc and not in_kc:
            if not (in_pc and not in_gc) and pIn and pIn < check_dt: loai_loi = "Thiếu KBLT (Chiều)"
        elif has_chieu and in_kc and not in_gc and out_c and out_c > check_dt:
            loai_loi = "Thiếu Opera (Chiều)"
        elif not has_chieu and in_gs and not in_ks and pIn and pIn <= check_dt:
            loai_loi = "Thiếu KBLT (Sáng)"
        elif not has_chieu and in_ps and not in_ks:
            loai_loi = "Chưa Khai Báo KBLT"

        if note.startswith(" | "): note = note[3:]

        row_data = {
            'Phòng': pRoom, 'Tên Khách': pName.upper(), 'Passport': pPass if 'NOPASS_' not in pPass else "",
            'Ngày In': format_date_vn(pIn), 'Ngày Out': format_date_vn(pOut),
            'Hạn Visa': format_date_vn(visa_dt) if visa_dt else "",
            'Trạng Thái/Ghi Chú': note.strip(), 
            'Hồ Sơ': ""
        }

        if loai_loi:
            rep_loi.append({**{'Phân Loại': loai_loi}, **row_data, 'Chi Tiết Lỗi': err})
        if is_due: rep_due.append(row_data)
        elif is_stay: rep_stay.append(row_data)

    return pd.DataFrame(rep_loi), pd.DataFrame(rep_stay), pd.DataFrame(rep_due)

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
    f_kblt_sang = st.file_uploader("KBLT Sáng (.xls/.xlsx)", type=['xls', 'xlsx'])
    f_gihf_sang = st.file_uploader("GIHF Sáng (.xml)", type=['xml'])
    f_pol_sang = st.file_uploader("Police Sáng (.xml)", type=['xml'])

with col2:
    st.subheader("🌙 CA CHIỀU")
    st.write("<br>", unsafe_allow_html=True)
    f_kblt_chieu = st.file_uploader("KBLT Chiều (.xls/.xlsx)", type=['xls', 'xlsx'])
    f_gihf_chieu = st.file_uploader("GIHF Chiều (.xml)", type=['xml'])
    f_pol_chieu = st.file_uploader("Police Chiều (.xml)", type=['xml'])

st.markdown("---")

if st.button("🚀 CHẠY KIỂM TRA ĐỐI CHIẾU", use_container_width=True):
    files = {
        'kblt_sang': f_kblt_sang, 'gihf_sang': f_gihf_sang, 'pol_sang': f_pol_sang,
        'kblt_chieu': f_kblt_chieu, 'gihf_chieu': f_gihf_chieu, 'pol_chieu': f_pol_chieu
    }
    
    if not any([f_kblt_sang, f_kblt_chieu]):
        st.error("Vui lòng nạp ít nhất 1 file KBLT (Sáng hoặc Chiều) để đối chiếu!")
    else:
        df_loi, df_stay, df_due = process_data(check_date, files)
        
        if not df_loi.empty: df_loi = df_loi.sort_values(by="Phòng")
        if not df_stay.empty: df_stay = df_stay.sort_values(by="Phòng")
        if not df_due.empty: df_due = df_due.sort_values(by="Phòng")

        tab1, tab2, tab3 = st.tabs(["🚨 Lỗi Dữ Liệu", "🛏️ Stayover", "🚪 Due Out"])
        
        with tab1:
            st.dataframe(df_loi, use_container_width=True)
        with tab2:
            st.dataframe(df_stay, use_container_width=True)
        with tab3:
            st.dataframe(df_due, use_container_width=True)
            
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_loi.to_excel(writer, sheet_name='Loi_DuLieu', index=False)
            df_stay.to_excel(writer, sheet_name='Stayover', index=False)
            df_due.to_excel(writer, sheet_name='Due Out', index=False)
        
        st.download_button(
            label="📥 Tải Báo Cáo Excel (Mang về máy chạy VBA quét Hồ sơ)",
            data=buffer.getvalue(),
            file_name=f"Bao_Cao_IMMI_{check_date.strftime('%d%m%Y')}.xlsx",
            mime="application/vnd.ms-excel"
        )