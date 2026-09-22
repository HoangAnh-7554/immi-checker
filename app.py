import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import io
import unicodedata
import pycountry

# ==========================================
# 0. KHỞI TẠO BIẾN TOÀN CỤC (TỐI ƯU HIỆU SUẤT)
# ==========================================
VN_MAP = {
    'LIÊN BANG NGA': 'RUS', 'NAM PHI': 'ZAF', 'VIỆT NAM': 'VNM', 'VN': 'VNM', 'AFGHANISTAN': 'AFG', 'AF': 'AFG', 
    'AILEN (IRELAND)': 'IRL', 'IE': 'IRL', 'ALGERIA': 'DZA', 'DZ': 'DZA', 'AMER.VIRGIN IS.': 'VIR', 'VI': 'VIR', 
    'AN BA NI': 'ALB', 'AL': 'ALB', 'ANDORRAN': 'AND', 'AD': 'AND', 'ANGOLA': 'AGO', 'AO': 'AGO', 'ANGUILLA': 'AIA', 
    'AI': 'AIA', 'ANH': 'GBR', 'GB': 'GBR', 'ANTARCTICA': 'ATA', 'AQ': 'ATA', 'ANTIGUA/BARBUDA': 'ATG', 'AG': 'ATG', 
    'ARGENTINA': 'ARG', 'AR': 'ARG', 'ARMENIA': 'ARM', 'AM': 'ARM', 'ARUBA': 'ABW', 'AW': 'ABW', 'AZERBAIJAN': 'AZE', 
    'AZ': 'AZE', 'ÁO': 'AUT', 'AT': 'AUT', 'ẤN ĐỘ': 'IND', 'IN': 'IND', 'BA LAN': 'POL', 'PL': 'POL', 'BAHAMAS': 'BHS', 
    'BS': 'BHS', 'BAHRAIN': 'BHR', 'BH': 'BHR', 'BAKER ISLAND': 'FQ', 'FQ': 'FQ', 'BANGLADESH': 'BGD', 'BD': 'BGD', 
    'BARBADOS': 'BRB', 'BB': 'BRB', 'BELARUS': 'BLR', 'BY': 'BLR', 'BELIZE': 'BLZ', 'BZ': 'BLZ', 'BENIN': 'BEN', 
    'BJ': 'BEN', 'BERMUDA': 'BMU', 'BM': 'BMU', 'BHUTAN': 'BTN', 'BT': 'BTN', 'BLUE': 'BLM', 'BL': 'BLM', 
    'BOLIVIA': 'BOL', 'BO': 'BOL', 'BOSNIA-HERZ.': 'BIH', 'BA': 'BIH', 'BOTSWANA': 'BWA', 'BW': 'BWA', 
    'BOUVET ISLANDS': 'BVT', 'BV': 'BVT', 'BRAZIL': 'BRA', 'BR': 'BRA', 'BRIT.IND.OC.TER': 'IOT', 'IO': 'IOT', 
    'BRIT.VIRGIN IS.': 'VGB', 'VG': 'VGB', 'BRUNEI DARUSS.': 'BRN', 'BN': 'BRN', 'BUN GA RI': 'BGR', 'BG': 'BGR', 
    'BURKINA FASO': 'BFA', 'BF': 'BFA', 'BURMA': 'MMR', 'MM': 'MMR', 'BURUNDI': 'BDI', 'BI': 'BDI', 
    'BẮC TRIỀU TIÊN': 'PRK', 'KP': 'PRK', 'BỈ': 'BEL', 'BE': 'BEL', 'BỒ ĐÀO NHA': 'PRT', 'PT': 'PRT', 
    'CA NA DA': 'CAN', 'CA': 'CAN', 'CAMEROON': 'CMR', 'CM': 'CMR', 'CAPE VERDE': 'CPV', 'CV': 'CPV', 
    'CAR': 'CAF', 'CF': 'CAF', 'CAYMAN ISLANDS': 'CYM', 'KY': 'CYM', 'CHAD': 'TCD', 'TD': 'TCD', 
    'CHANNEL ISLANDS': 'CP', 'CP': 'CP', 'CHILE': 'CHL', 'CL': 'CHL', 'CHRISTMAS ISLAN': 'KT', 'KT': 'KT', 
    'CHRISTMAS ISLND': 'CXR', 'CX': 'CXR', 'CLIPPERTON ISLA': 'IP', 'IP': 'IP', 'COCONUT ISLANDS': 'CCK', 'CC': 'CCK', 
    'COLUMBIA': 'COL', 'CO': 'COL', 'COMOROS': 'COM', 'KM': 'COM', 'COOK ISLANDS': 'COK', 'CK': 'COK', 
    'CORSICA': 'VP', 'VP': 'VP', 'COSTA RICA': 'CRI', 'CR': 'CRI', 'COTE D\'IVOIRE': 'CIV', 'CI': 'CIV', 
    'CUBA': 'CUB', 'CU': 'CUB', 'CYPRUS': 'CYP', 'CY': 'CYP', 'CĂMPUCHIA': 'KHM', 'KH': 'KHM', 'CAMPUCHIA': 'KHM', 'CĂM PU CHIA': 'KHM',
    'DEM. REP. CONGO': 'COD', 'CD': 'COD', 'DJIBOUTI': 'DJI', 'DJ': 'DJI', 'DOMINICA': 'DMA', 'DM': 'DMA', 
    'DOMINICAN REP.': 'DOM', 'DO': 'DOM', 'DUTCH ANTILLES': 'AN', 'AN': 'AN', 'ĐAN MẠCH': 'DNK', 'DK': 'DNK', 
    'ĐÀI LOAN': 'TWN', 'TW': 'TWN', 'ĐỨC': 'DEU', 'DE': 'DEU', 'EAST TIMOR': 'TP', 'TL': 'TLS', 'ECUADOR': 'ECU', 
    'EC': 'ECU', 'EGYPT': 'EGY', 'EG': 'EGY', 'EL SALVADOR': 'SLV', 'SV': 'SLV', 'EQUATORIAL GUIN': 'GNQ', 
    'GQ': 'GNQ', 'ERITREA': 'ERI', 'ER': 'ERI', 'ESTONIA': 'EST', 'EE': 'EST', 'ETHIOPIA': 'ETH', 'ET': 'ETH', 
    'EUROPEAN UNION': 'EU', 'EU': 'EU', 'FALKLAND ISLNDS': 'FLK', 'FK': 'FLK', 'FAROE ISLANDS': 'FRO', 'FO': 'FRO', 
    'FIJI': 'FJI', 'FJ': 'FJI', 'FINLAND': 'FIN', 'FI': 'FIN', 'FRANCE, METROPO': 'FX', 'FRENC.POLYNESIA': 'PYF', 
    'PF': 'PYF', 'FRENCH GUAYANA': 'GUF', 'GF': 'GUF', 'FRENCH S.TERRIT': 'ATF', 'TF': 'ATF', 'FRENCH SOUTHERN': 'FS', 
    'GABON': 'GAB', 'GA': 'GAB', 'GAMBIA': 'GMB', 'GM': 'GMB', 'GAZA STRIP': 'GZ', 'GEORGIA': 'GEO', 'GE': 'GEO', 
    'GHANA': 'GHA', 'GH': 'GHA', 'GIBRALTAR': 'GIB', 'GI': 'GIB', 'GLORIOSO ISLAND': 'GO', 'GREECE': 'GRC', 
    'GR': 'GRC', 'GREENLAND': 'GRL', 'GL': 'GRL', 'GRENADA': 'GRD', 'GD': 'GRD', 'GUADELOUPE': 'GLP', 'GP': 'GLP', 
    'GUAM': 'GUM', 'GU': 'GUM', 'GUATEMALA': 'GTM', 'GT': 'GTM', 'GUERNSEY': 'GGY', 'GK': 'GGY', 'GUINEA': 'GIN', 
    'GN': 'GIN', 'GUINEA-BISSAU': 'GNB', 'GW': 'GNB', 'GUYANA': 'GUY', 'GY': 'GUY', 'HAITI': 'HTI', 'HT': 'HTI', 
    'HEARD/MCDON.ISL': 'HMD', 'HM': 'HMD', 'HOA KỲ': 'USA', 'US': 'USA', 'HONDURAS': 'HND', 'HN': 'HND', 
    'HONG KONG': 'HKG', 'HK': 'HKG', 'HOWLAND ISLAND': 'HQ', 'HUNG GA RI': 'HUN', 'HU': 'HUN', 'HÀ LAN': 'NLD', 
    'NL': 'NLD', 'HÀN QUỐC': 'KOR', 'KR': 'KOR', 'I TA LI A': 'ITA', 'IT': 'ITA', 'ICELAND': 'ISL', 'IS': 'ISL', 
    'INDONESIA': 'IDN', 'ID': 'IDN', 'IRAN': 'IRN', 'IR': 'IRN', 'IRAQ': 'IRQ', 'IQ': 'IRQ', 'ISLE OF MAN': 'IMN', 
    'IM': 'IMN', 'ISRAEL': 'ISR', 'IL': 'ISR', 'JAMAICA': 'JAM', 'JM': 'JAM', 'JAN MAYEN': 'JN', 'JAPAN RYUKYU': 'JA', 
    'JARVIS ISLAND': 'DQ', 'JERSEY': 'JEY', 'JE': 'JEY', 'JOHNSTON ATOLL': 'JQ', 'JORDAN': 'JOR', 'JO': 'JOR', 
    'JUAN DE NOVA IS': 'JU', 'KAZAKHSTAN': 'KAZ', 'KZ': 'KAZ', 'KENYA': 'KEN', 'KE': 'KEN', 'KINGMAN REEF': 'KQ', 
    'KIRIBATI': 'KIR', 'KI': 'KIR', 'KUWAIT': 'KWT', 'KW': 'KWT', 'KYRGYZSTAN': 'KGZ', 'KG': 'KGZ', 'LATVIA': 'LVA', 
    'LV': 'LVA', 'LEBANON': 'LBN', 'LB': 'LBN', 'LESOTHO': 'LSO', 'LS': 'LSO', 'LIBERIA': 'LBR', 'LR': 'LBR', 
    'LIBI': 'LBY', 'LY': 'LBY', 'LIECHTENSTEIN': 'LIE', 'LI': 'LIE', 'LITHUANIA': 'LTU', 'LT': 'LTU', 
    'LUXEMBOURG': 'LUX', 'LU': 'LUX', 'LÀO': 'LAO', 'LA': 'LAO', 'MACAU': 'MAC', 'MO': 'MAC', 'MACEDONIA': 'MKD', 
    'MK': 'MKD', 'MADAGASCAR': 'MDG', 'MG': 'MDG', 'MALAWI': 'MWI', 'MW': 'MWI', 'MALAYSIA': 'MYS', 'MY': 'MYS', 
    'MALDIVES': 'MDV', 'MV': 'MDV', 'MALI': 'MLI', 'ML': 'MLI', 'MALTA': 'MLT', 'MT': 'MLT', 'MARSHALL ISLNDS': 'MHL', 
    'MH': 'MHL', 'MARTINIQUE': 'MTQ', 'MQ': 'MTQ', 'MAURETANIA': 'MRT', 'MR': 'MRT', 'MAURITIUS': 'MUS', 'MU': 'MUS', 
    'MAYOTTE': 'MYT', 'YT': 'MYT', 'MEXICO': 'MEX', 'MX': 'MEX', 'MICRONESIA': 'FSM', 'FM': 'FSM', 
    'MINOR OUTL.ISL.': 'UMI', 'UM': 'UMI', 'MOLDOVA': 'MDA', 'MD': 'MDA', 'MONACO': 'MCO', 'MC': 'MCO', 
    'MONTENEGRO': 'MNE', 'ME': 'MNE', 'MONTSERRAT': 'MSR', 'MS': 'MSR', 'MOROCCO': 'MAR', 'MA': 'MAR', 
    'MOZAMBIQUE': 'MOZ', 'MZ': 'MOZ', 'MÔNG CỔ': 'MNG', 'MN': 'MNG', 'N.MARIANA ISLND': 'MNP', 'MP': 'MNP', 
    'NAM TƯ': 'HRV', 'HR': 'HRV', 'NAMIBIA': 'NAM', 'NA': 'NAM', 'NATO': 'NT', 'NAURU': 'NRU', 'NR': 'NRU', 
    'NAVASSA ISLAND': 'BQ', 'NEPAL': 'NPL', 'NP': 'NPL', 'NEW CALEDONIA': 'NCL', 'NC': 'NCL', 'NEW ZEALAND': 'NZL', 
    'NZ': 'NZL', 'NGA': 'RUS', 'RU': 'RUS', 'NHẬT': 'JPN', 'JP': 'JPN', 'NICARAGUA': 'NIC', 'NI': 'NIC', 'NIGER': 'NER', 
    'NE': 'NER', 'NIGERIA': 'NGA', 'NG': 'NGA', 'NIUE': 'NIU', 'NU': 'NIU', 'NORFOLK ISLANDS': 'NFK', 'NF': 'NFK', 
    'NORWAY': 'NOR', 'NO': 'NOR', 'OMAN': 'OMN', 'OM': 'OMN', 'ORANGE': 'OR', 'OTHER COUNTRY': 'OC', 'PAKISTAN': 'PAK', 
    'PK': 'PAK', 'PALAU': 'PLW', 'PW': 'PLW', 'PALESTINE': 'PSE', 'PS': 'PSE', 'PALMYRA ATOLL': 'LQ', 'PANAMA': 'PAN', 
    'PA': 'PAN', 'PAP. NEW GUINEA': 'PNG', 'PG': 'PNG', 'PARAGUAY': 'PRY', 'PY': 'PRY', 'PERU': 'PER', 'PE': 'PER', 
    'PHILIPPIN': 'PHL', 'PH': 'PHL', 'PHÁP': 'FRA', 'FR': 'FRA', 'PITCAIRN ISLNDS': 'PCN', 'PN': 'PCN', 
    'PUERTO RICO': 'PRI', 'PR': 'PRI', 'QATAR': 'QAT', 'QA': 'QAT', 'REP.OF CONGO': 'COG', 'CG': 'COG', 
    'REUNION': 'REU', 'RE': 'REU', 'RU MA NI': 'ROU', 'RO': 'ROU', 'RWANDA': 'RWA', 'RW': 'RWA', 'S. SANDWICH INS': 'SGS', 
    'GS': 'SGS', 'S.TOME,PRINCIPE': 'STP', 'ST': 'STP', 'SAINT HELENA': 'SHN', 'SH': 'SHN', 'SAMOA': 'WSM', 'WS': 'WSM', 
    'SAMOA, AMERICA': 'ASM', 'AS': 'ASM', 'SAN MARINO': 'SMR', 'SM': 'SMR', 'SAUDI ARABIA': 'SAU', 'SA': 'SAU', 
    'SENEGAL': 'SEN', 'SN': 'SEN', 'SERBIA': 'SRB', 'RS': 'SRB', 'SERBIA MTNEGRO': 'YU', 'SERBIA/MONTEN.': 'CS', 
    'SEYCHELLES': 'SYC', 'SC': 'SYC', 'SIERRA LEONE': 'SLE', 'SL': 'SLE', 'SINGAPORE': 'SGP', 'SG': 'SGP', 
    'SLOVAKIA': 'SVK', 'SK': 'SVK', 'SLOVENIA': 'SVN', 'SI': 'SVN', 'SOLOMON ISLANDS': 'SLB', 'SB': 'SLB', 
    'SOMALIA': 'SOM', 'SO': 'SOM', 'SOUTH AFRICA': 'ZAF', 'ZA': 'ZAF', 'SRI LANKA': 'LKA', 'LK': 'LKA', 
    'ST KITTS NEVIS': 'KNA', 'KN': 'KNA', 'ST. LUCIA': 'LCA', 'LC': 'LCA', 'ST. VINCENT': 'VCT', 'VC': 'VCT', 
    'ST.PIER,MIQUEL.': 'SPM', 'PM': 'SPM', 'SUDAN': 'SDN', 'SD': 'SDN', 'SURINAME': 'SUR', 'SR': 'SUR', 'SVALBARD': 'SJM', 
    'SJ': 'SJM', 'SWAZILAND': 'SWZ', 'SZ': 'SWZ', 'SWITZERLAND': 'CHE', 'CH': 'CHE', 'SYRIA': 'SYR', 'SY': 'SYR', 
    'SÉC': 'CZE', 'CZ': 'CZE', 'TAJIKISTAN': 'TJK', 'TJ': 'TJK', 'TANZANIA': 'TZA', 'TZ': 'TZA', 'THÁI LAN': 'THA', 
    'TH': 'THA', 'THỤY ĐIỂN': 'SWE', 'SE': 'SWE', 'TOGO': 'TGO', 'TG': 'TGO', 'TOKELAU ISLANDS': 'TKL', 'TK': 'TKL', 
    'TONGA': 'TON', 'TO': 'TON', 'TRINIDAD,TOBAGO': 'TTO', 'TT': 'TTO', 'TROMELIN ISLAND': 'TE', 'TRUNG QUỐC': 'CHN', 
    'CN': 'CHN', 'TUNISIA': 'TUN', 'TN': 'TUN', 'TURKEY': 'TUR', 'TR': 'TUR', 'TURKMENISTAN': 'TKM', 'TM': 'TKM', 
    'TURKSH CAICOSIN': 'TCA', 'TC': 'TCA', 'TUVALU': 'TUV', 'TV': 'TUV', 'TÂY BAN NHA': 'ESP', 'ES': 'ESP', 
    'UGANDA': 'UGA', 'UG': 'UGA', 'UKRAINE': 'UKR', 'UA': 'UKR', 'UNITED ARAB EMI': 'ARE', 'UE': 'UE', 
    'UNITED NATIONS': 'UN', 'UNKNOWN COUNTRY': 'UC', 'URUGUAY': 'URY', 'UY': 'URY', 'UTD.ARAB EMIR.': 'ARE', 'AE': 'ARE', 
    'UZBEKISTAN': 'UZB', 'UZ': 'UZB', 'ÚC': 'AUS', 'AU': 'AUS', 'VANUATU': 'VUT', 'VU': 'VUT', 'VATICAN CITY': 'VAT', 
    'VA': 'VAT', 'VENEZUELA': 'VEN', 'VE': 'VEN', 'WALLIS,FUTUNA': 'WLF', 'WF': 'WLF', 'WEST SAHARA': 'ESH', 'EH': 'ESH', 
    'YEMEN': 'YEM', 'YE': 'YEM', 'ZAMBIA': 'ZMB', 'ZM': 'ZMB', 'ZIMBABWE': 'ZWE', 'ZW': 'ZWE', 'KHÁC': 'ZZ', 
    'TRUNG QUỐC (ĐÀI LOAN)': 'TWN', 'CH HÀN': 'KOR', 'VƯƠNG QUỐC ANH VÀ BẮC AI LEN': 'GBR', 'VƯƠNG QUỐC ANH': 'GBR', 
    'UK': 'GBR', 'Ô-XTRÂY-LI-A': 'AUS', 'Ô-XTRÂY': 'AUS', 'MA-LAI-XI-A': 'MYS', 'MA-LAI': 'MYS', 'XIN-GA-PO': 'SGP', 
    'XIN-GA': 'SGP', 'IN-ĐÔ-NÊ-XI-A': 'IDN', 'IN-ĐÔ-NÊ': 'IDN', 'CA-NA-DA': 'CAN', 'MÊ-XI-CÔ': 'MEX', 'HỒNG KÔNG': 'HKG', 
    'THỔ NHĨ KỲ': 'TUR', 'THỔ NHĨ': 'TUR', 'VƯƠNG QUỐC NA-UY': 'NOR', 'ÁC-HEN-TI-NA': 'ARG', 'AC-HEN-TI-NA': 'ARG', 
    'ITALIA': 'ITA', 'AI LÊN': 'IRL', 'NƯU TÂY LAN': 'NZL', 'CĂM-PU-CHIA': 'KHM', 'BĂNG-LA-ĐÉT': 'BGD', 'NÊ-PAN': 'NPL', 
    'PA-KÍT-XTAN': 'PAK', 'NI-GIÊ-RI-A': 'NGA', 'MA-RỐC': 'MAR', 'AN-GIÊ-RI': 'DZA', 'BÊ-LA-RÚT': 'BLR',
    'CH LIÊN BANG ĐỨC': 'DEU', 'CỘNG HÒA LIÊN BANG ĐỨC': 'DEU', 'CỘNG HOÀ LIÊN BANG ĐỨC': 'DEU',
    'NHẬT BẢN': 'JPN', 'MỸ': 'USA', 'FX': 'FRA', 'RQ': 'RUS', 'PHILIPPINES': 'PHL', 'CANADA': 'CAN', 'NA UY': 'NOR', 
    'Ý': 'ITA', 'THỤY SĨ': 'CHE', 'PHẦN LAN': 'FIN', 'HY LẠP': 'GRC', 'IRELAND': 'IRL', 'MYANMAR': 'MMR', 'MA CAO': 'MAC', 
    'TRIỀU TIÊN': 'PRK', 'CU BA': 'CUB', 'COLOMBIA': 'COL', 'CÔ-LÔM-BI-A': 'COL', 'CHI-LÊ': 'CHL', 'AI CẬP': 'EGY', 
    'UAE': 'ARE', 'CÁC TIỂU VƯƠNG QUỐC': 'ARE', 'Ả RẬP XÊ ÚT': 'SAU', 'U-CRAI-NA': 'UKR', 'MARỐC': 'MAR', 'ZAIRE': 'COD', 'ZR': 'COD'
}
VN_MAP_KEYS_SORTED = sorted(VN_MAP.keys(), key=len, reverse=True)

# ==========================================
# 1. CÁC HÀM XỬ LÝ LÕI VÀ ĐỒNG BỘ DỮ LIỆU
# ==========================================

def get_src_name(s_key):
    """Đổi tên nhãn nguồn dữ liệu cho dễ nhìn"""
    s_lower = s_key.lower()
    if 'kblt' in s_lower: return 'KBLT'
    if 'gihf' in s_lower: return 'Opera'
    if 'pol' in s_lower: return 'Police'
    return s_key

def get_srcs_str(s_keys):
    """Gộp chung các nguồn trùng nhau (VD: KBLT+Opera)"""
    return '+'.join(dict.fromkeys(get_src_name(s) for s in s_keys))

def safe_str(val):
    if pd.isna(val) or val is None or str(val).strip().lower() in ['nan', 'none']: return ""
    return str(val).strip()

def safe_room(r_val):
    r = safe_str(r_val)
    r_stripped = r.lstrip('0')
    return (r_stripped if r_stripped else r).split('.')[0]

def standardize_text(txt):
    txt = safe_str(txt)
    if not txt: return ""
    return unicodedata.normalize('NFC', txt).upper()

def clean_name(name):
    name = standardize_text(name).replace("*", "").replace(",", " ").replace(".", " ")
    name = re.sub(r'\b(MR|MS|MRS)\b', '', name)
    return " ".join(re.sub(r'[^A-Z ]', '', name).split())

def is_same_guest(name1, name2):
    n1, n2 = clean_name(name1), clean_name(name2)
    if n1 == n2 or n1.replace(" ","") == n2.replace(" ",""): return True
    if len(n1) > 8 and len(n2) > 8 and (n1.replace(" ","") in n2.replace(" ","") or n2.replace(" ","") in n1.replace(" ","")): return True
    arr1 = [w for w in n1.split() if len(w) >= 2 and w not in ["BIN", "BINTI", "THI", "VAN", "THE"]]
    arr2 = [w for w in n2.split() if len(w) >= 2 and w not in ["BIN", "BINTI", "THI", "VAN", "THE"]]
    return sum(1 for w in arr1 if w in arr2) >= 2 or (len(arr1) <= 1 and sum(1 for w in arr1 if w in arr2) >= 1)

def std_gender(g):
    g = standardize_text(g)
    if not g: return ""
    if g in ['M', 'NAM', 'MR.', 'MR', 'MALE']: return 'NAM'
    if g in ['F', 'NỮ', 'NU', 'MS', 'MRS.', 'MRS', 'FEMALE', 'MISS']: return 'NỮ'
    return g

def get_iso3(val):
    val = standardize_text(val)
    if not val: return ""
    if val in VN_MAP: return VN_MAP[val]
    for vn_name in VN_MAP_KEYS_SORTED:
        if len(vn_name) >= 4 and vn_name in val: return VN_MAP[vn_name]
    try: return pycountry.countries.lookup(val).alpha_3
    except LookupError: return val

def match_nationality(nat1, nat2):
    if not nat1 or not nat2: return False
    n1, n2 = standardize_text(nat1), standardize_text(nat2)
    if n1 == n2: return True
    iso1, iso2 = get_iso3(n1), get_iso3(n2)
    if iso1 == iso2: return True
    if {iso1, iso2}.issubset({'CHN', 'HKG'}) or {iso1, iso2}.issubset({'CHN', 'MAC'}): return True
    return False

def is_dob_match(d1, d2):
    if pd.isna(d1) and pd.isna(d2): return True
    if pd.isna(d1) or pd.isna(d2): return False
    if d1 == d2: return True
    
    def get_y(d):
        if isinstance(d, datetime): return d.year
        if isinstance(d, str) and d.isdigit() and len(d) == 4: return int(d)
        return None
        
    y1, y2 = get_y(d1), get_y(d2)
    if y1 and y2 and y1 == y2:
        is_jan1_1 = isinstance(d1, datetime) and d1.month == 1 and d1.day == 1
        is_jan1_2 = isinstance(d2, datetime) and d2.month == 1 and d2.day == 1
        is_str_1 = isinstance(d1, str)
        is_str_2 = isinstance(d2, str)
        if is_jan1_1 or is_jan1_2 or is_str_1 or is_str_2: return True
    return False

def parse_date(val, is_dob=False):
    if pd.isna(val) or val is None: return None
    val_str = str(val).strip()
    if val_str.lower() in ["nan", "nat", "none", ""]: return None
    
    if isinstance(val, datetime): return val.replace(tzinfo=None)
    if hasattr(val, 'to_pydatetime'):
        try: return val.to_pydatetime().replace(tzinfo=None)
        except: pass
        
    try: return datetime.strptime(val_str.upper(), '%d-%b-%y').replace(tzinfo=None)
    except:
        try: return datetime.strptime(val_str.upper(), '%d-%b-%Y').replace(tzinfo=None)
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
# 2. ĐỌC DỮ LIỆU TỪ CÁC FILE
# ==========================================

def parse_kblt_excel(file):
    try:
        df = pd.read_excel(file, header=9)
        df['Ngày sinh'] = df.get('Ngày sinh', df.get('Năm sinh', pd.Series(dtype=str))).apply(lambda x: parse_date(x, is_dob=True))
        df['Giới tính'] = df.get('GT', df.get('Giới tính', pd.Series(dtype=str))).apply(std_gender)
        df['Quốc tịch'] = df.get('QT', df.get('Quốc tịch', pd.Series(dtype=str))).apply(standardize_text)
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
                'Họ tên': safe_str(name.text if name is not None else "").replace('*', '').strip(),
                'Ngày sinh': parse_date(dob.text, is_dob=True) if dob is not None else None,
                'Giới tính': std_gender(gender.text if gender is not None else ""),
                'Quốc tịch': standardize_text(nat.text if nat is not None else ""),
                'Số hộ chiếu': standardize_text(passport.text if passport is not None else ""),
                'Ngày đến ': parse_date(din.text) if din is not None else None,
                'Thời gian dự kiến tạm trú tại CSLT': parse_date(dout.text) if dout is not None else None,
                'Thời hạn được phép tạm trú tại Việt Nam': parse_date(visa.text) if visa is not None else None,
                'Số phòng': safe_room(room.text if room is not None else "")
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Lỗi đọc XML: {e}")
        return pd.DataFrame()

# ==========================================
# 3. ĐỐI CHIẾU DỮ LIỆU ĐA CHIỀU
# ==========================================
def process_data(check_date, files_dict):
    st.info("Đang tiến hành phân tích và soi chiếu đa chiều...")
    dfs = {k: (parse_xml(v, is_police=('pol_' in k)) if v.name.endswith('.xml') else parse_kblt_excel(v)) if v else pd.DataFrame() for k, v in files_dict.items()}
            
    all_guests = []
    for source_label, df in dfs.items():
        if not df.empty:
            for _, r in df.iterrows():
                room = safe_room(r.get('Số phòng'))
                name = safe_str(r.get('Họ tên'))
                passp = standardize_text(safe_str(r.get('Số hộ chiếu')))
                
                if not passp or passp == 'NAN': passp = f"NOPASS_{room}_{name[:5]}"
                
                din, dout = r.get('Ngày đến '), r.get('Thời gian dự kiến tạm trú tại CSLT')
                visa = r.get('Thời hạn được phép tạm trú tại Việt Nam', None)
                
                all_guests.append({
                    'Key': passp, 'Room': room, 'Name': name, 'DOB': r.get('Ngày sinh'), 
                    'Gender': r.get('Giới tính'), 'Nat': r.get('Quốc tịch'),
                    'In': din, 'Out': dout, 'Visa': visa, 'Src': source_label
                })

    master_dict = {}
    for g in all_guests:
        found_key = None
        for k, v in master_dict.items():
            if "NOPASS_" not in g['Key'] and "NOPASS_" not in k and g['Key'] == k:
                found_key = k
                break
            elif v['Room'] == g['Room'] and is_same_guest(v['Name'], g['Name']):
                found_key = k
                break
                
        if not found_key:
            found_key = g['Key']
            master_dict[found_key] = {'Room': g['Room'], 'Name': g['Name'], 'Key': g['Key'], 'Srcs': {}}
            
        master_dict[found_key]['Srcs'][g['Src']] = g

    uploaded_files = [k for k, v in files_dict.items() if v is not None]
    has_ca_truoc = any(s in uploaded_files for s in ['kblt_sang', 'gihf_sang', 'pol_sang'])
    has_ca_hien_tai = any(s in uploaded_files for s in ['kblt_chieu', 'gihf_chieu', 'pol_chieu'])
    
    rep_loi, rep_stay, rep_due = [], [], []
    check_dt = datetime.combine(check_date, datetime.min.time())

    for key, data in master_dict.items():
        srcs = data['Srcs']
        base_src = next((srcs[s] for s in ['kblt_chieu', 'gihf_chieu', 'kblt_sang', 'gihf_sang', 'pol_chieu', 'pol_sang'] if s in srcs), None)
        if not base_src: continue

        pRoom, pName = data['Room'], base_src['Name']
        all_outs = [srcs[s]['Out'] for s in srcs if pd.notna(srcs[s].get('Out')) and not isinstance(srcs[s]['Out'], str)]
        chot_out_date = max(all_outs) if all_outs else None
        
        err = ""
        
        # 1. Quét biến động Số Phòng
        rooms = []
        room_srcs = {}
        for s in srcs:
            r = safe_str(srcs[s].get('Room'))
            if r:
                if r not in rooms:
                    rooms.append(r)
                    room_srcs[r] = []
                room_srcs[r].append(s)
        
        final_room_display = " ➔ ".join(rooms) if len(rooms) > 1 else (rooms[0] if rooms else pRoom)
        if len(rooms) > 1: 
            diff = " vs ".join([f"{get_srcs_str(room_srcs[r])}: {r}" for r in rooms])
            err += f"Lệch/Đổi Phòng ({diff}); "
        
        # 2. Quét Tên
        names = []
        name_srcs = {}
        for s in srcs:
            n = safe_str(srcs[s].get('Name'))
            if n:
                matched_n = next((ex_n for ex_n in names if is_same_guest(n, ex_n)), None)
                if matched_n:
                    name_srcs[matched_n].append(s)
                else:
                    names.append(n)
                    name_srcs[n] = [s]
        if len(names) > 1: 
            diff = " vs ".join([f"{get_srcs_str(name_srcs[n])}: {n}" for n in names])
            err += f"Lệch Tên ({diff}); "
        
        # 3. Quét Passport
        passes = []
        pass_srcs = {}
        for s in srcs:
            p = safe_str(srcs[s].get('Key'))
            if p and "NOPASS_" not in p:
                if p not in passes:
                    passes.append(p)
                    pass_srcs[p] = []
                pass_srcs[p].append(s)
        if len(passes) > 1: 
            diff = " vs ".join([f"{get_srcs_str(pass_srcs[p])}: {p}" for p in passes])
            err += f"Lệch Hộ chiếu ({diff}); "
            
        # 4. Quét Quốc tịch
        nats = []
        nat_srcs = {}
        for s in srcs:
            nt = safe_str(srcs[s].get('Nat'))
            if nt:
                matched_nt = next((ex_nt for ex_nt in nats if match_nationality(nt, ex_nt)), None)
                if matched_nt:
                    nat_srcs[matched_nt].append(s)
                else:
                    nats.append(nt)
                    nat_srcs[nt] = [s]
        if len(nats) > 1: 
            diff = " vs ".join([f"{get_srcs_str(nat_srcs[nt])}: {nt}" for nt in nats])
            err += f"Lệch Quốc tịch ({diff}); "
            
        # 5. Quét Ngày sinh
        dobs = []
        dob_srcs = {}
        for s in srcs:
            d = srcs[s].get('DOB')
            if pd.notna(d):
                matched_d = next((ex_d for ex_d in dobs if is_dob_match(d, ex_d)), None)
                if matched_d:
                    dob_srcs[matched_d].append(s)
                else:
                    dobs.append(d)
                    dob_srcs[d] = [s]
        if len(dobs) > 1: 
            diff = " vs ".join([f"{get_srcs_str(dob_srcs[d])}: {format_date_vn(d)}" for d in dobs])
            err += f"Lệch Ngày sinh ({diff}); "
            
        # 6. Quét Ngày In
        ins = []
        in_srcs = {}
        for s in srcs:
            d = srcs[s].get('In')
            if pd.notna(d):
                if d not in ins:
                    ins.append(d)
                    in_srcs[d] = []
                in_srcs[d].append(s)
        if len(ins) > 1: 
            diff = " vs ".join([f"{get_srcs_str(in_srcs[d])}: {format_date_vn(d)}" for d in ins])
            err += f"Lệch Ngày In ({diff}); "
            
        # 7. Quét Ngày Out
        outs = []
        out_srcs = {}
        for s in srcs:
            d = srcs[s].get('Out')
            if pd.notna(d):
                if d not in outs:
                    outs.append(d)
                    out_srcs[d] = []
                out_srcs[d].append(s)
        if len(outs) > 1: 
            diff = " vs ".join([f"{get_srcs_str(out_srcs[d])}: {format_date_vn(d)}" for d in outs])
            err += f"Biến động Ngày Out/Extend ({diff}); "
            
        # 8. Quét Hạn Visa
        visas = []
        visa_srcs = {}
        for s in srcs:
            d = srcs[s].get('Visa')
            if pd.notna(d) and isinstance(d, datetime):
                if d not in visas:
                    visas.append(d)
                    visa_srcs[d] = []
                visa_srcs[d].append(s)
        if len(visas) > 1: 
            diff = " vs ".join([f"{get_srcs_str(visa_srcs[d])}: {format_date_vn(d)}" for d in visas])
            err += f"Lệch Hạn Visa ({diff}); "

        is_due, is_stay, note, loai_loi = False, False, "", ""
        if has_ca_hien_tai:
            if base_src.get('In') == check_dt:
                if chot_out_date == check_dt: is_due, note = True, "[Day-use] Khách in/out trong ngày"
                else: is_stay, note = True, "Khách mới Check-in"
            else:
                if chot_out_date == check_dt: is_due, note = True, "Dự kiến Due Out (Chú ý Check-out trên KBLT)"
                elif chot_out_date and chot_out_date > check_dt: is_stay = True
        else:
            if base_src.get('In') == check_dt: is_stay, note = True, "Khách mới Check-in"
            elif chot_out_date == check_dt: is_due, note = True, "Dự kiến Due Out"
            else: is_stay = True

        pVisa = None
        for v in visas:
            if isinstance(v, datetime): 
                if pVisa is None or v > pVisa: pVisa = v

        is_visa_expired_now = False
        if pVisa and isinstance(pVisa, datetime):
            days_to_check = (pVisa - check_dt).days
            if days_to_check < 0: 
                is_visa_expired_now = True
                err += f"Khách đã hết hạn Visa từ {format_date_vn(pVisa)}; "
            elif chot_out_date and pd.notna(chot_out_date) and pVisa < chot_out_date:
                msg = f"Visa ({format_date_vn(pVisa)}) HẾT HẠN trước Ngày Out ({format_date_vn(chot_out_date)})!"
                note += f" | 🚨 [Cảnh Báo] {msg}"
                err += f"[Cảnh Báo] {msg}; "
            elif days_to_check <= 7: 
                msg = f"Visa sắp hết hạn ({format_date_vn(pVisa)}) - Còn {days_to_check} ngày."
                note += f" | ⚠️ [Sắp hết hạn] {msg}"
                err += f"[Sắp hết hạn] {msg}; "

        final_passport = passes[0] if passes else ""
        
        nopass_srcs = [s for s in srcs if 'NOPASS_' in srcs[s]['Key']]
        if nopass_srcs:
            loai_loi = "Thiếu Passport"
            err = f"Chưa nhập số Passport trên {get_srcs_str(nopass_srcs)}; " + err

        if not pRoom or pRoom == "0" or pRoom.upper() == "PM": 
            loai_loi = "Trống Số Phòng"
            err = "Chưa gán phòng; " + err

        if is_visa_expired_now: loai_loi = "Visa Hết Hạn"
        elif err: 
            if "[Cảnh Báo]" in err: loai_loi = "Cảnh Báo Visa"
            else: loai_loi = "Lưu ý"
        else:
            is_vietnamese = any(get_iso3(srcs[s]['Nat']) == 'VNM' for s in srcs if srcs[s]['Nat'])
            if has_ca_hien_tai:
                if 'gihf_chieu' in uploaded_files and 'gihf_chieu' not in srcs:
                    if chot_out_date and chot_out_date > check_dt: loai_loi = "Thiếu Opera (Hiện tại)"
                if 'kblt_chieu' in uploaded_files and 'kblt_chieu' not in srcs:
                    if chot_out_date and chot_out_date > check_dt: loai_loi = "Thiếu KBLT (Hiện tại)"
                if not is_vietnamese and 'pol_chieu' in uploaded_files and 'pol_chieu' not in srcs:
                    if chot_out_date and chot_out_date > check_dt: loai_loi = "Thiếu Police (Hiện tại)"
            elif has_ca_truoc:
                if 'gihf_sang' in uploaded_files and 'gihf_sang' not in srcs: loai_loi = "Thiếu Opera (Ca trước)"
                if 'kblt_sang' in uploaded_files and 'kblt_sang' not in srcs: loai_loi = "Thiếu KBLT (Ca trước)"
                if not is_vietnamese and 'pol_sang' in uploaded_files and 'pol_sang' not in srcs: loai_loi = "Thiếu Police (Ca trước)"

        if not is_vietnamese:
            opera_missing = False
            opera_garbage = []
            for s in srcs:
                if 'gihf' in s:
                    v = srcs[s]['Visa']
                    if pd.isna(v):
                        opera_missing = True
                    elif isinstance(v, str) and v.upper() not in ["MIỄN", "EXEMPT", "K/T", "-"]:
                        opera_missing = True
                        if v not in opera_garbage: opera_garbage.append(v)
            
            if opera_missing:
                loai_loi = "Lưu ý" if not loai_loi else loai_loi
                if opera_garbage:
                    err += f"Chưa nhập Visa trên Opera (Đang chứa dữ liệu rác: {', '.join(opera_garbage)}); "
                else:
                    err += "Chưa nhập Visa trên Opera; "

        if note.startswith(" | "): note = note[3:]

        row_data = {
            'Phân Loại': loai_loi if loai_loi else "",
            'Phòng': final_room_display, 
            'Tên Khách': base_src['Name'].upper(), 
            'Passport': final_passport,
            'Ngày sinh': format_date_vn(base_src['DOB']), 
            'Giới tính': base_src['Gender'], 
            'Quốc tịch': base_src['Nat'],
            'Ngày In': format_date_vn(base_src.get('In')), 
            'Ngày Out': format_date_vn(chot_out_date),
            'Hạn Visa': format_date_vn(pVisa),
            'Trạng Thái/Ghi Chú': note.strip(), 
            'Chi Tiết': err, 'Hồ Sơ': ""
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
# 4. GIAO DIỆN STREAMLIT (UI)
# ==========================================
st.set_page_config(page_title="Tool Check IMMI", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>PULLMAN VŨNG TÀU - ĐỐI CHIẾU IMMI ĐA CHIỀU</h1>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("☀️ DỮ LIỆU CA TRƯỚC (Ví dụ: Ca Đêm/Sáng)")
    check_date = st.date_input("Ngày kiểm tra báo cáo:", format="DD/MM/YYYY")
    fk_s = st.file_uploader("KBLT Ca Trước (.xls/.xlsx)", type=['xls', 'xlsx'])
    fg_s = st.file_uploader("Opera GIHF Ca Trước (.xml)", type=['xml'])
    fp_s = st.file_uploader("Police Ca Trước (.xml)", type=['xml'])
with col2:
    st.subheader("🌙 DỮ LIỆU HIỆN TẠI (Ví dụ: Ca Sáng/Chiều)")
    st.write("<br>", unsafe_allow_html=True)
    fk_c = st.file_uploader("KBLT Hiện Tại (.xls/.xlsx)", type=['xls', 'xlsx'])
    fg_c = st.file_uploader("Opera GIHF Hiện Tại (.xml)", type=['xml'])
    fp_c = st.file_uploader("Police Hiện Tại (.xml)", type=['xml'])

st.markdown("---")

def color_warning(val):
    if not isinstance(val, str): return ''
    val_up = val.upper()
    if "[CẢNH BÁO]" in val_up: return 'color: #D32F2F; font-weight: bold'
    if "[SẮP HẾT HẠN]" in val_up: return 'color: #F57C00; font-weight: bold'
    return ''

if st.button("🚀 CHẠY KIỂM TRA TỔNG HỢP", use_container_width=True):
    files = {'kblt_sang': fk_s, 'gihf_sang': fg_s, 'pol_sang': fp_s, 'kblt_chieu': fk_c, 'gihf_chieu': fg_c, 'pol_chieu': fp_c}
    
    if not any([fk_s, fg_s, fp_s, fk_c, fg_c, fp_c]):
        st.error("Vui lòng nạp ít nhất 1 file để đối chiếu!")
    else:
        df_loi, df_stay, df_due = process_data(check_date, files)
        
        cols = ['Phòng', 'Tên Khách', 'Passport', 'Ngày sinh', 'Giới tính', 'Quốc tịch', 'Ngày In', 'Ngày Out', 'Hạn Visa']
        final_loi_cols = ['Phân Loại'] + cols + ['Chi Tiết', 'Hồ Sơ']
        final_stay_cols = cols + ['Trạng Thái/Ghi Chú', 'Hồ Sơ']
        
        if df_loi.empty: df_loi = pd.DataFrame(columns=final_loi_cols)
        else: df_loi = sort_rooms(df_loi)[final_loi_cols]
        
        if df_stay.empty: df_stay = pd.DataFrame(columns=final_stay_cols)
        else: df_stay = sort_rooms(df_stay)[final_stay_cols]
        
        if df_due.empty: df_due = pd.DataFrame(columns=final_stay_cols)
        else: df_due = sort_rooms(df_due)[final_stay_cols]

        tab1, tab2, tab3 = st.tabs(["📌 Lưu Ý (Báo lỗi)", "🛏️ Khách Lưu Trú (Stayover)", "🚪 Dự kiến Trả Phòng (Due Out)"])
        with tab1: st.dataframe(df_loi, use_container_width=True)
        with tab2: st.dataframe(df_stay.style.map(color_warning, subset=['Trạng Thái/Ghi Chú']), use_container_width=True)
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