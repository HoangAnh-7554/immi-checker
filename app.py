import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import io

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
    match_count = sum(1 for w in arr1 if w in arr2)
    return match_count >= 2 or (len(arr1) <= 1 and match_count >= 1)

def convert_opera_date(op_date):
    try: return datetime.strptime(str(op_date).strip(), '%d-%b-%y') if op_date and not pd.isna(op_date) else None
    except: return None

def extract_visa_date(txt):
    if pd.isna(txt) or not txt: return None
    match = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b', str(txt).strip())
    if match:
        d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if y < 100: y += 2000
        try: return datetime(y, m, d)
        except: return None
    return None

def format_date_vn(dt):
    return dt.strftime('%d/%m/%Y') if not pd.isna(dt) and dt is not None and not isinstance(dt, str) else ("" if pd.isna(dt) else dt)

def parse_kblt_excel(file):
    try:
        df = pd.read_excel(file, header=9)
        df['Thời hạn được phép tạm trú tại Việt Nam'] = df['Thời hạn được phép tạm trú tại Việt Nam'].apply(lambda x: x if extract_visa_date(x) else None)
        return df
    except Exception as e:
        st.error(f"Lỗi đọc KBLT Excel: {e}")
        return pd.DataFrame()

def parse_opera_xml(file):
    try:
        root = ET.parse(file).getroot()
        data = []
        for nd in root.findall('.//G_C9'):
            name = nd.find('C12').text if nd.find('C12') is not None else (nd.find('C15').text if nd.find('C15') is not None else "")
            data.append({
                'Họ tên': name.replace('*', ''),
                'Số hộ chiếu': nd.find('C30').text if nd.find('C30') is not None else "",
                'Số phòng': str(nd.find('C42').text).strip().lstrip('0') if nd.find('C42') is not None else "",
                'Ngày đến ': convert_opera_date(nd.find('C36').text if nd.find('C36') is not None else (nd.find('C42').text if nd.find('C42') is not None else "")),
                'Thời gian dự kiến tạm trú tại CSLT': convert_opera_date(nd.find('C39').text if nd.find('C39') is not None else (nd.find('C45').text if nd.find('C45') is not None else "")),
                'Thời hạn được phép tạm trú tại Việt Nam': nd.find('C33').text if nd.find('C33') is not None else ""
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Lỗi đọc XML: {e}")
        return pd.DataFrame()

def process_data(check_date, files_dict):
    st.info("Đang tiến hành đối chiếu dữ liệu...")
    dfs = {k: (parse_opera_xml(v) if v.name.endswith('.xml') else parse_kblt_excel(v)) if v else pd.DataFrame() for k, v in files_dict.items()}
    all_guests = []
    
    def extract_info(df, src_lbl):
        res = []
        if not df.empty:
            for _, r in df.iterrows():
                room = str(r.get('Số phòng', '')).strip().split('.')[0]
                name = str(r.get('Họ tên', '')).strip()
                passp = str(r.get('Số hộ chiếu', '')).strip()
                if not passp or passp == 'nan': passp = f"NOPASS_{room}_{name[:5]}"
                din, dout = r.get('Ngày đến '), r.get('Thời gian dự kiến tạm trú tại CSLT')
                res.append({'Key': passp, 'Room': room, 'Name': name, 'In': extract_visa_date(din) if isinstance(din, str) else din, 'Out': extract_visa_date(dout) if isinstance(dout, str) else dout, 'Visa': str(r.get('Thời hạn được phép tạm trú tại Việt Nam', '')).strip(), 'Src': src_lbl})
        return res

    for k in dfs.keys(): all_guests.extend(extract_info(dfs[k], k))
    
    master = {}
    for g in all_guests:
        fk = next((k for k, v in master.items() if v['Room'] == g['Room'] and is_same_guest(v['Name'], g['Name'])), g['Key']) if g['Key'] not in master else g['Key']
        if fk not in master: master[fk] = {'Room': g['Room'], 'Name': g['Name'], 'Pass': g['Key'], 'Srcs': {}}
        master[fk]['Srcs'][g['Src']] = g

    has_c = not dfs['kblt_chieu'].empty or not dfs['gihf_chieu'].empty
    rep_loi, rep_stay, rep_due = [], [], []

    for key, d in master.items():
        srcs = d['Srcs']
        in_ks, in_gs, in_ps = 'kblt_sang' in srcs, 'gihf_sang' in srcs, 'pol_sang' in srcs
        in_kc, in_gc, in_pc = 'kblt_chieu' in srcs, 'gihf_chieu' in srcs, 'pol_chieu' in srcs
        b_src = next((srcs[s] for s in ['kblt_chieu', 'gihf_chieu', 'kblt_sang', 'gihf_sang', 'pol_chieu', 'pol_sang'] if s in srcs), None)
        if not b_src: continue

        pRoom, pName, pPass, pIn, pOut, pVisa = d['Room'], b_src['Name'], b_src['Pass'], b_src['In'], b_src['Out'], b_src['Visa']
        out_s = srcs['kblt_sang']['Out'] if in_ks else (srcs['gihf_sang']['Out'] if in_gs else None)
        out_c = srcs['kblt_chieu']['Out'] if in_kc else (srcs['gihf_chieu']['Out'] if in_gc else None)
        is_due, is_stay, note, err, loai = False, False, "", "", ""
        cdt = datetime.combine(check_date, datetime.min.time())
        
        if has_c:
            if pIn == cdt or in_pc:
                if (in_kc and out_c == cdt) or (not in_kc and not in_gc and out_s == cdt): is_due, note = True, "[Day-use] Khách in/out trong ngày"
                else: is_stay, note = True, "Khách mới Check-in" if not pIn or pIn >= cdt else "Khách Check-in hôm qua"
            if in_ks or in_gs:
                if out_s == cdt:
                    if not in_kc and not in_gc: is_due, note = True, "Đã Checked-out hoàn toàn"
                    elif out_c and out_c > cdt: is_stay, note = True, f"[Extend] Gia hạn thêm đến {format_date_vn(out_c)}"
                    else: is_due, note = True, "Chưa Checked-out"
                elif out_s and out_s > cdt:
                    if not in_kc and not in_gc: is_due, note = True, "[Shorten] Trả phòng sớm"
                    else:
                        is_stay = True
                        if out_c and out_c > out_s: note = f"[Extend] Gia hạn thêm đến {format_date_vn(out_c)}"
                        elif out_c and out_c < out_s and out_c == cdt: is_stay, is_due, note = False, True, "[Shorten] Trả phòng sớm"
            if not any([in_ks, in_gs, in_ps, in_pc]):
                 if out_c == cdt: is_due = True 
                 else: is_stay = True
        else:
            if pIn == cdt or in_ps: is_stay, note = True, "Khách Check-in hôm qua" if pIn and pIn < cdt else "Khách mới Check-in"
            if in_ks or in_gs:
                if out_s == cdt: is_due, note = True, "Dự kiến Due Out"
                elif out_s and out_s > cdt: is_stay = True

        vdt = extract_visa_date(pVisa)
        if vdt:
            dl = (vdt - cdt).days
            if dl < 0: note += " | [VISA HẾT HẠN]"
            elif dl <= 7: note += f" | [Visa còn {dl} ngày]"

        b_dict, c_dict, n_b, n_c = None, None, "", ""
        if has_c and in_kc and in_gc: b_dict, c_dict, n_b, n_c = srcs['kblt_chieu'], srcs['gihf_chieu'], "Web", "Opera"
        elif not has_c and in_ks and in_gs: b_dict, c_dict, n_b, n_c = srcs['kblt_sang'], srcs['gihf_sang'], "Web", "Opera"
        elif not has_c and in_ks and in_ps: b_dict, c_dict, n_b, n_c = srcs['kblt_sang'], srcs['pol_sang'], "Web", "Police"

        if b_dict and c_dict:
            if b_dict['Room'] != c_dict['Room']: err += f"Lệch Phòng ({n_b}: {b_dict['Room']} vs {n_c}: {c_dict['Room']}); "
            if b_dict['Out'] != c_dict['Out']: err += f"Lệch Ngày Out ({n_b}: {format_date_vn(b_dict['Out'])} vs {n_c}: {format_date_vn(c_dict['Out'])}); "
            if not is_same_guest(b_dict['Name'], c_dict['Name']): err += f"Lệch Tên ({n_b}: {b_dict['Name']} vs {n_c}: {c_dict['Name']}); "

        if 'NOPASS_' in pPass: loai, err = "Thiếu Passport", "Chưa nhập số Passport; "
        if not pRoom or pRoom == "0" or pRoom.upper() == "PM": loai, err = "Trống Số Phòng", err + "Chưa gán phòng; "

        if err: loai = loai or "Lệch Dữ Liệu"
        elif has_c and in_gc and not in_kc:
            if not (in_pc and not in_gc) and pIn and pIn < cdt: loai = "Thiếu KBLT (Chiều)"
        elif has_c and in_kc and not in_gc and out_c and out_c > cdt: loai = "Thiếu Opera (Chiều)"
        elif not has_c and in_gs and not in_ks and pIn and pIn <= cdt: loai = "Thiếu KBLT (Sáng)"
        elif not has_c and in_ps and not in_ks: loai = "Chưa Khai Báo KBLT"

        if note.startswith(" | "): note = note[3:]

        row_data = {
            'Phòng': pRoom, 'Tên Khách': pName.upper(), 'Passport': pPass if 'NOPASS_' not in pPass else "",
            'Ngày In': format_date_vn(pIn), 'Ngày Out': format_date_vn(pOut),
            'Hạn Visa': format_date_vn(vdt) if vdt else "",
            'Trạng Thái/Ghi Chú': note.strip(), 'Hồ Sơ': "" # Để trống chờ VBA quét
        }
        if loai: rep_loi.append({**{'Phân Loại': loai}, **row_data, 'Chi Tiết Lỗi': err})
        if is_due: rep_due.append(row_data)
        elif is_stay: rep_stay.append(row_data)

    return pd.DataFrame(rep_loi), pd.DataFrame(rep_stay), pd.DataFrame(rep_due)

st.set_page_config(page_title="Tool Check IMMI", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>PULLMAN VŨNG TÀU - TOOL ĐỐI CHIẾU IMMI</h1>", unsafe_allow_html=True)
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    st.subheader("☀️ CA SÁNG")
    check_date = st.date_input("Ngày kiểm tra:", format="DD/MM/YYYY")
    fk_s = st.file_uploader("KBLT Sáng", type=['xls', 'xlsx'])
    fg_s = st.file_uploader("GIHF Sáng", type=['xml'])
    fp_s = st.file_uploader("Police Sáng", type=['xml'])
with c2:
    st.subheader("🌙 CA CHIỀU")
    st.write("<br>", unsafe_allow_html=True)
    fk_c = st.file_uploader("KBLT Chiều", type=['xls', 'xlsx'])
    fg_c = st.file_uploader("GIHF Chiều", type=['xml'])
    fp_c = st.file_uploader("Police Chiều", type=['xml'])

st.markdown("---")
if st.button("🚀 CHẠY KIỂM TRA ĐỐI CHIẾU", use_container_width=True):
    files = {'kblt_sang': fk_s, 'gihf_sang': fg_s, 'pol_sang': fp_s, 'kblt_chieu': fk_c, 'gihf_chieu': fg_c, 'pol_chieu': fp_c}
    if not any([fk_s, fk_c]): st.error("Vui lòng nạp ít nhất 1 file KBLT (Sáng hoặc Chiều)!")
    else:
        df_l, df_s, df_d = process_data(check_date, files)
        if not df_l.empty: df_l = df_l.sort_values("Phòng")
        if not df_s.empty: df_s = df_s.sort_values("Phòng")
        if not df_d.empty: df_d = df_d.sort_values("Phòng")

        t1, t2, t3 = st.tabs(["🚨 Lỗi Dữ Liệu", "🛏️ Stayover", "🚪 Due Out"])
        with t1: st.dataframe(df_l, use_container_width=True)
        with t2: st.dataframe(df_s, use_container_width=True)
        with t3: st.dataframe(df_d, use_container_width=True)
            
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            df_l.to_excel(w, sheet_name='Loi_DuLieu', index=False)
            df_s.to_excel(w, sheet_name='Stayover', index=False)
            df_d.to_excel(w, sheet_name='Due Out', index=False)
        st.download_button("📥 Tải Báo Cáo Excel (Mang về máy chạy VBA quét Hồ sơ)", data=buf.getvalue(), file_name=f"Bao_Cao_IMMI_{check_date.strftime('%d%m%Y')}.xlsx", mime="application/vnd.ms-excel")
