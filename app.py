import streamlit as st
import pandas as pd
import urllib.request
import xml.etree.ElementTree as ET
from itertools import combinations
from datetime import datetime
import time

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(
    page_title="SPMD — Volební Štáb LIVE Domažlice 2026", 
    layout="wide", 
    page_icon="🏛️",
    initial_sidebar_state="collapsed"
)

REFRESH_INTERVAL = 60

# --- PŘESNÉ BAREVNÉ SCHÉMA STRAN ---
PARTY_COLORS = {
    "STRANA PRO DOMAŽLICE": "#d97706",
    "Pro Domažlice, KDU-ČSL a nezávislí": "#d97706",
    "VAŠE DOMAŽLICE": "#58c6ff",
    "Stačilo! (KSČM a nezávislí)": "#dc2626",
    "ANO 2011 a nezávislí": "#adefee",
    "ANO 2011 s podporou nezávislých": "#adefee",
    "Česká pirátská strana": "#7e22ce",
    "Občanská demokratická strana": "#2563eb",
    "SDRUŽENÍ PRO MĚSTO DOMAŽLICE": "#026a7f",
    "ŽIJEME DOMAŽLICE - VÝZVA PRO NOVÝ SMĚR MĚSTA": "#16a34a",
    "Svoboda a přímá demokracie (SPD)": "#b91c1c"
}

def get_party_color(party_name):
    p_clean = party_name.replace('\u200b', '').strip()
    if p_clean in PARTY_COLORS:
        return PARTY_COLORS[p_clean]
    for k, v in PARTY_COLORS.items():
        if k.lower() in p_clean.lower() or p_clean.lower() in k.lower():
            return v
    return "#475569"

def hex_to_rgba(hex_code, alpha=0.18):
    hex_code = hex_code.lstrip('#')
    if len(hex_code) == 6:
        r, g, b = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {alpha})"
    return "rgba(241, 245, 249, 1)"

# --- CSS STYLY ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700;800;900&family=JetBrains+Mono:wght@700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .robust-summary-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 2px solid #334155;
        border-radius: 12px;
        padding: 12px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .summary-title {
        color: #ffffff;
        font-size: 1.3rem;
        font-weight: 900;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
    }
    .summary-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 8px 12px;
    }
    .summary-label {
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .summary-value {
        font-size: 1.4rem;
        font-weight: 900;
        color: #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        line-height: 1.1;
    }

    .rep-card-box {
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 6px;
        min-height: 72px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.08);
        border-top: 1px solid rgba(0,0,0,0.05);
        border-right: 1px solid rgba(0,0,0,0.05);
        border-bottom: 1px solid rgba(0,0,0,0.05);
    }
    .rep-name {
        font-size: 0.92rem;
        font-weight: 900;
        color: #0f172a;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2;
    }
    .rep-party {
        font-size: 0.75rem;
        font-weight: 700;
        color: #334155;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2;
    }
    .rep-foot {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .rep-votes {
        font-size: 0.82rem;
        font-weight: 900;
        color: #0284c7;
    }
    .rep-pred-votes {
        font-size: 0.75rem;
        font-weight: 800;
        color: #0d9488;
    }

    .trend-pill {
        font-size: 0.72rem;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .trend-up { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
    .trend-down { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
    .trend-same { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
    .trend-new { background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; }

    .blur-overlay {
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        z-index: 999999;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .celebration-card {
        background: linear-gradient(135deg, #026a7f 0%, #0369a1 100%);
        border: 4px solid #38bdf8;
        border-radius: 24px;
        padding: 40px;
        text-align: center;
        color: white;
        max-width: 750px;
        width: 90%;
    }
    .shot-timer-bar {
        height: 6px;
        background: #38bdf8;
        border-radius: 3px;
        margin-top: 20px;
        animation: countdown 5s linear forwards;
    }
    @keyframes countdown {
        from { width: 100%; }
        to { width: 0%; }
    }
    .food-modal {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        border: 2px solid #fcd34d;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def prehrat_oslavny_zvuk():
    sound_url = "https://assets.mixkit.co/active_storage/sfx/2018/2018-preview.mp3"
    st.markdown(f'<audio autoplay style="display:none;"><source src="{sound_url}" type="audio/mp3"></audio>', unsafe_allow_html=True)

# --- NAČÍTÁNÍ Z ČSÚ ---
@st.cache_data(ttl=REFRESH_INTERVAL)
def nacti_kompletni_csu_data(url, kod_zastup="553425"):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        raw_bytes = urllib.request.urlopen(req, timeout=10).read()
        root = ET.fromstring(raw_bytes)
        
        target_obec = None
        for elem in root.iter():
            if elem.attrib.get('KODZASTUP') == kod_zastup:
                target_obec = elem
                break
                
        if target_obec is None:
            return None, f"V XML nebyl nalezen uzel s KODZASTUP='{kod_zastup}'."

        strany_list, zvoleni_kandidati_list, vsechni_kandidati_list = [], [], []
        
        for elem in target_obec.iter():
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag_name == 'VOLEBNI_STRANA':
                attr = elem.attrib
                nazev_strany = attr.get('NAZEV_STRANY', '').strip()
                hlasy_strany = int(attr.get('HLASY', 0))
                proc_strany = float(attr.get('HLASY_PROC', 0.0))
                mandaty_strany = int(attr.get('ZASTUPITELE_POCET', 0))

                strany_list.append({
                    "Kandidátní listina": nazev_strany,
                    "Celkem hlasů": hlasy_strany,
                    "Podíl (%)": proc_strany,
                    "Mandáty ČSÚ": mandaty_strany
                })

                for kand in elem.iter():
                    k_tag = kand.tag.split('}')[-1] if '}' in kand.tag else kand.tag
                    if k_tag in ['ZASTUPITEL', 'KANDIDAT']:
                        k_attr = kand.attrib
                        celkovo_jmeno = f"{k_attr.get('TITULPRED', '')} {k_attr.get('JMENO', '')} {k_attr.get('PRIJMENI', '')} {k_attr.get('TITULZA', '')}".strip()
                        is_zvolen = (k_tag == 'ZASTUPITEL')

                        cand_obj = {
                            "Poř.": int(k_attr.get('PORADOVE_CISLO', 0)),
                            "Jméno a příjmení": celkovo_jmeno,
                            "Kandidátní listina": nazev_strany,
                            "Preferenční hlasy": int(k_attr.get('HLASY', 0)),
                            "Podíl hlasů (%)": float(k_attr.get('HLASY_PROC', 0.0)),
                            "Zvolen": is_zvolen
                        }

                        if is_zvolen:
                            cand_obj["Status"] = "✅ Získal mandát"
                            zvoleni_kandidati_list.append(cand_obj)

                        vsechni_kandidati_list.append(cand_obj)

        ucast_data = {}
        for elem in target_obec.iter():
            u_tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if u_tag == 'UCAST':
                u_attr = elem.attrib
                ucast_data = {
                    "okrsky_celkem": int(u_attr.get('OKRSKY_CELKEM', 0)),
                    "okrsky_zprac": int(u_attr.get('OKRSKY_ZPRAC', 0)),
                    "okrsky_proc": float(u_attr.get('OKRSKY_ZPRAC_PROC', 0.0)),
                    "zapsani_volici": int(u_attr.get('ZAPSANI_VOLICI', 0)),
                    "vydane_obalky": int(u_attr.get('VYDANE_OBALKY', 0)),
                    "platne_hlasy": int(u_attr.get('PLATNE_HLASY', 0)),
                    "ucast_proc": float(u_attr.get('UCAST_PROC', 0.0))
                }

        return {
            "strany": strany_list,
            "zvoleni_kandidati": zvoleni_kandidati_list,
            "vsechni_kandidati": vsechni_kandidati_list,
            "ucast": ucast_data
        }, None

    except Exception as e:
        return None, f"Chyba při načítání XML: {e}"

def vypocitej_mandaty(hlasy_dict, celkem_mandatu=21, hranice_pct=5.0):
    celkem_hlasu = sum(hlasy_dict.values())
    if celkem_hlasu == 0: return {}, {}
    pct_dict = {strana: (h / celkem_hlasu * 100) for strana, h in hlasy_dict.items()}
    platne = {strana: h for strana, h in hlasy_dict.items() if pct_dict[strana] >= hranice_pct}
    podily = []
    for strana, h in platne.items():
        for i in range(1, celkem_mandatu + 1):
            podily.append((h / i, strana))
    podily.sort(key=lambda x: x[0], reverse=True)
    mandaty = {strana: 0 for strana in hlasy_dict.keys()}
    for i in range(min(celkem_mandatu, len(podily))):
        mandaty[podily[i][1]] += 1
    return mandaty, pct_dict

def vypocitej_predikce(hlasy_dict, ucast_data, kandidati_list):
    pct_zprac = ucast_data.get('okrsky_proc', 0.0)
    if pct_zprac == 0:
        return hlasy_dict, vypocitej_mandaty(hlasy_dict)[0], kandidati_list, "⚪ Čeká se na 1. okrsek"

    koeficient = 100.0 / pct_zprac
    pred_hlasy_strany = {strana: int(h * koeficient) for strana, h in hlasy_dict.items()}
    pred_mandaty, _ = vypocitej_mandaty(pred_hlasy_strany)

    pred_kandidati = []
    for k in kandidati_list:
        k_copy = k.copy()
        k_copy["Preferenční hlasy (predikce)"] = int(k.get("Preferenční hlasy", 0) * koeficient)
        pred_kandidati.append(k_copy)

    if pct_zprac < 30: jistota_txt = "🔴 Nízká spolehlivost"
    elif pct_zprac < 70: jistota_txt = "🟡 Střední spolehlivost"
    elif pct_zprac < 100: jistota_txt = "🟢 Vysoká spolehlivost"
    else: jistota_txt = "🏁 Finální (100 %)"

    return pred_hlasy_strany, pred_mandaty, pred_kandidati, jistota_txt

def najdi_koalice(mandaty, min_kresel=11, zakazane=[], povinne=[]):
    strany = [s for s, m in mandaty.items() if m > 0 and s not in zakazane]
    vysledky = []
    for r in range(1, len(strany) + 1):
        for combo in combinations(strany, r):
            if not all(p in combo for p in povinne): continue
            kresla = sum(mandaty[s] for s in combo)
            if kresla >= min_kresel:
                is_minimal = True
                for s in combo:
                    if s not in povinne and (kresla - mandaty[s]) >= min_kresel:
                        is_minimal = False; break
                if is_minimal:
                    if kresla == 11: status_class, status_txt = "badge-krehka", "🔴 Křehká většina (11)"
                    elif kresla in [12, 13]: status_class, status_txt = "badge-bezpecna", "🟢 Bezpečná většina (12–13)"
                    else: status_class, status_txt = "badge-dominantni", "🔵 Svrchovaná většina (14+)"
                    vysledky.append((combo, kresla, status_txt, status_class))
    vysledky.sort(key=lambda x: (x[1], len(x[0])))
    return vysledky

# --- VESTAVĚNÁ DATA KANDIDÁTEK 2026 ---
@st.cache_data
def nacti_kandidatky_2026_built_in():
    try:
        df_csv = pd.read_csv('data-export.csv', sep=';', encoding='utf-8-sig')
        df_csv.columns = [c.strip() for c in df_csv.columns]
        party_col = 'Kandidátní listina.název'
        name_col = 'Kandidát.příjmení, jméno, tituly'
        num_col = 'Kandidát.poř. číslo'
        df_csv[party_col] = df_csv[party_col].astype(str).str.replace('\u200b', '').str.strip()
        df_csv[name_col] = df_csv[name_col].astype(str).str.replace('\u200b', '').str.strip()
        df_csv[num_col] = pd.to_numeric(df_csv[num_col], errors='coerce').fillna(0).astype(int)
        return df_csv
    except Exception:
        built_in_kands = [
            {"Kandidátní listina.číslo": 1, "Kandidátní listina.název": "VAŠE DOMAŽLICE", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Krutina Viktor Ing.", "Kandidát.věk": 48, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "1. místostarosta města Domažlice", "Bydliště": "Dolejší Předměstí"},
            {"Kandidátní listina.číslo": 1, "Kandidátní listina.název": "VAŠE DOMAŽLICE", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Štangl Jiří", "Kandidát.věk": 48, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "hlavní mistr", "Bydliště": "Dolejší Předměstí"},
            {"Kandidátní listina.číslo": 1, "Kandidátní listina.název": "VAŠE DOMAŽLICE", "Kandidát.poř. číslo": 3, "Kandidát.příjmení, jméno, tituly": "Špoták Rudolf", "Kandidát.věk": 43, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "emeritní hejtman Plzeňského kraje", "Bydliště": "Bezděkovské Předměstí"},
            {"Kandidátní listina.číslo": 4, "Kandidátní listina.název": "Pro Domažlice, KDU-ČSL a nezávislí", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Bc. Stanislav Antoš", "Kandidát.věk": 59, "Navrhující strana": "KDU-ČSL", "Politická příslušnost": "KDU-ČSL", "Povolání": "starosta města Domažlice", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 4, "Kandidátní listina.název": "Pro Domažlice, KDU-ČSL a nezávislí", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Vorlíček Marek MgA.", "Kandidát.věk": 47, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "varhanář, sbormistr, radní", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 4, "Kandidátní listina.název": "Pro Domažlice, KDU-ČSL a nezávislí", "Kandidát.poř. číslo": 3, "Kandidát.příjmení, jméno, tituly": "Kadlec Ivo MUDr.", "Kandidát.věk": 71, "Navrhující strana": "KDU-ČSL", "Politická příslušnost": "BEZPP", "Povolání": "zubní lékař", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Wiesner Radek, Ing.", "Kandidát.věk": 47, "Navrhující strana": "ANO", "Politická příslušnost": "ANO", "Povolání": "konstruktér, manažer výroby", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Pauler David, Mgr.", "Kandidát.věk": 45, "Navrhující strana": "ANO", "Politická příslušnost": "ANO", "Povolání": "pedagog, podnikatel", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 3, "Kandidát.příjmení, jméno, tituly": "Piták Martin, Mgr.", "Kandidát.věk": 41, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "manažer", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 4, "Kandidát.příjmení, jméno, tituly": "Bor David", "Kandidát.věk": 44, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "OSVČ", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 5, "Kandidát.příjmení, jméno, tituly": "Látka Jan", "Kandidát.věk": 72, "Navrhující strana": "ANO", "Politická příslušnost": "ANO", "Povolání": "senátor", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Mgr. Kamil Jindřich", "Kandidát.věk": 53, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "hudebník, učitel", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Josef Kuneš", "Kandidát.věk": 47, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "ředitel ZUŠ", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 3, "Kandidát.příjmení, jméno, tituly": "Mgr. Ivan Rybár", "Kandidát.věk": 60, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "ředitel základní školy Domažlice", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 4, "Kandidát.příjmení, jméno, tituly": "Novák Zdeněk JUDr.", "Kandidát.věk": 74, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "emeritní starosta, důchodce", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 5, "Kandidát.příjmení, jméno, tituly": "Ing. Zbyněk Wolf", "Kandidát.věk": 52, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "projektant", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 6, "Kandidátní listina.název": "Občanská demokratická strana", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Faschingbauer Pavel, Ing.", "Kandidát.věk": 53, "Navrhující strana": "ODS", "Politická příslušnost": "ODS", "Povolání": "ekonom", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 6, "Kandidátní listina.název": "Občanská demokratická strana", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Mgr. Jakub Faschingbauer", "Kandidát.věk": 33, "Navrhující strana": "ODS", "Politická příslušnost": "BEZPP", "Povolání": "lékárník", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 8, "Kandidátní listina.název": "ŽIJEME DOMAŽLICE - VÝZVA PRO NOVÝ SMĚR MĚSTA", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Hradecká Hana Mgr. et Mgr.", "Kandidát.věk": 59, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "středoškolská učitelka VOŠ, OA a SZŠ Domažlice", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 8, "Kandidátní listina.název": "ŽIJEME DOMAŽLICE - VÝZVA PRO NOVÝ SMĚR MĚSTA", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Piták Luboš Mgr.", "Kandidát.věk": 62, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "OSVČ, právník", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 9, "Kandidátní listina.název": "Svoboda a přímá demokracie (SPD)", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Obdržálek Michal", "Kandidát.věk": 36, "Navrhující strana": "SPD", "Politická příslušnost": "SPD", "Povolání": "živnostník v pohostinství, zastupitel města", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 5, "Kandidátní listina.název": "Česká pirátská strana", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Pachl Jan", "Kandidát.věk": 47, "Navrhující strana": "PIRÁTI", "Politická příslušnost": "PIRÁTI", "Povolání": "sklenář - OSVČ", "Bydliště": "Domažlice"}
        ]
        return pd.DataFrame(built_in_kands)

df_kandidatky_2026 = nacti_kandidatky_2026_built_in()

# --- SIDEBAR & SIMULAČNÍ CENTRUM ---
st.sidebar.markdown("### 📡 Zdroj ČSÚ Data")
url_live = st.sidebar.text_input(
    "URL Živá XML data:", 
    value="https://volby.gov.cz/appdata/kv2026/20261009/odata/okresy/vysledky_obce_okres_CZ0321.xml"
)

if "is_simulation_active" not in st.session_state: st.session_state["is_simulation_active"] = False
if "simulated_bonus_mandate" not in st.session_state: st.session_state["simulated_bonus_mandate"] = 0
if "trigger_food_now" not in st.session_state: st.session_state["trigger_food_now"] = False
if "show_shot_modal" not in st.session_state: st.session_state["show_shot_modal"] = False
if "last_spmd_mandates" not in st.session_state: st.session_state["last_spmd_mandates"] = 0

if st.sidebar.button("🔮 Spustit Simulaci Volby 2026"):
    st.session_state["is_simulation_active"] = True
    st.session_state["show_shot_modal"] = True
    st.rerun()

if st.sidebar.button("🥃 Simulovat nový mandát pro SPMD (+Zvuk)"):
    st.session_state["simulated_bonus_mandate"] += 1
    st.session_state["show_shot_modal"] = True
    st.rerun()

if st.sidebar.button("🍕 Simulovat hlášku k jídlu"):
    st.session_state["trigger_food_now"] = True
    st.rerun()

if st.sidebar.button("🔄 Návrat k živým datům (Reset)"):
    st.session_state["is_simulation_active"] = False
    st.session_state["simulated_bonus_mandate"] = 0
    st.session_state["trigger_food_now"] = False
    st.session_state["show_shot_modal"] = False
    st.rerun()

# NAČTENÍ DAT
data_live, err_live = nacti_kompletni_csu_data(url_live, kod_zastup="553425")
data_past, _ = nacti_kompletni_csu_data("https://volby.gov.cz/pls/kv2022/vysledky_obce_okres?datumvoleb=20220923&nuts=CZ0321", kod_zastup="553425")

past_mandates = {s["Kandidátní listina"]: s["Mandáty ČSÚ"] for s in data_past["strany"]} if data_past else {}
past_votes_kand = {k["Jméno a příjmení"]: k["Preferenční hlasy"] for k in data_past["vsechni_kandidati"]} if data_past else {}

# PRÁCE S MODELI / DATA
if st.session_state["is_simulation_active"]:
    sim_votes = {
        "SDRUŽENÍ PRO MĚSTO DOMAŽLICE": 14700,
        "ANO 2011 a nezávislí": 14700,
        "Pro Domažlice, KDU-ČSL a nezávislí": 9500,
        "Občanská demokratická strana": 7200,
        "VAŠE DOMAŽLICE": 6300,
        "ŽIJEME DOMAŽLICE - VÝZVA PRO NOVÝ SMĚR MĚSTA": 5600,
        "Svoboda a přímá demokracie (SPD)": 4900,
        "Česká pirátská strana": 3800,
        "Stačilo! (KSČM a nezávislí)": 2800
    }
    
    mandates_calc, pct_calc = vypocitej_mandaty(sim_votes)
    if "SDRUŽENÍ PRO MĚSTO DOMAŽLICE" in mandates_calc:
        mandates_calc["SDRUŽENÍ PRO MĚSTO DOMAŽLICE"] += st.session_state["simulated_bonus_mandate"]

    ucast_render = {
        "okrsky_celkem": 12, "okrsky_zprac": 5, "okrsky_proc": 41.67,
        "zapsani_volici": 8214, "vydane_obalky": 3777, "platne_hlasy": sum(sim_votes.values()),
        "ucast_proc": 45.98
    }

    # Sestavení zvolených kandidátů z vestavěné databáze pro simulaci
    zvoleni_list = []
    if df_kandidatky_2026 is not None:
        p_col = 'Kandidátní listina.název'
        n_col = 'Kandidát.příjmení, jméno, tituly'
        num_col = 'Kandidát.poř. číslo'
        
        for party, m_count in mandates_calc.items():
            if m_count <= 0: continue
            party_kands = df_kandidatky_2026[
                df_kandidatky_2026[p_col].str.contains(party[:10], case=False, na=False, regex=False)
            ].sort_values(by=num_col)
            
            if party_kands.empty:
                for i in range(1, m_count + 1):
                    zvoleni_list.append({
                        "Poř.": i, "Jméno a příjmení": f"Kandidát #{i} ({party})",
                        "Kandidátní listina": party, "Preferenční hlasy": int(sim_votes[party] / 15) - i * 10,
                        "Podíl hlasů (%)": 5.0, "Zvolen": True, "Status": "✅ Získal mandát"
                    })
            else:
                for idx, (_, row) in enumerate(party_kands.iterrows()):
                    if idx >= m_count: break
                    jmeno = row[n_col]
                    poradi = row[num_col]
                    pref_votes = max(100, int(sim_votes[party] / 21) + (21 - poradi) * 35)
                    zvoleni_list.append({
                        "Poř.": poradi, "Jméno a příjmení": jmeno, "Kandidátní listina": party,
                        "Preferenční hlasy": pref_votes, "Podíl hlasů (%)": round((pref_votes / sim_votes[party]) * 100, 2),
                        "Zvolen": True, "Status": "✅ Získal mandát"
                    })

    # Výpočet predikcí
    pred_hlasy, pred_mandaty, pred_kandidati, spolehlivost_txt = vypocitej_predikce(sim_votes, ucast_render, zvoleni_list)

    df_strany_render = pd.DataFrame([
        {
            "Kandidátní listina": k, 
            "Celkem hlasů": v, 
            "Podíl (%)": pct_calc[k], 
            "Mandáty (aktuální)": mandates_calc[k],
            "Mandáty (predikce 100%)": pred_mandaty.get(k, 0)
        }
        for k, v in sim_votes.items()
    ])

else:
    if data_live and data_live["strany"]:
        df_strany_render = pd.DataFrame(data_live["strany"])
        hlasy_dict = dict(zip(df_strany_render["Kandidátní listina"], df_strany_render["Celkem hlasů"]))
        mandates_calc, pct_calc = vypocitej_mandaty(hlasy_dict)
        
        if "SDRUŽENÍ PRO MĚSTO DOMAŽLICE" in mandates_calc:
            mandates_calc["SDRUŽENÍ PRO MĚSTO DOMAŽLICE"] += st.session_state["simulated_bonus_mandate"]
            
        df_strany_render["Mandáty (aktuální)"] = df_strany_render["Kandidátní listina"].map(mandates_calc)
        ucast_render = data_live["ucast"]

        # Výpočet predikce
        pred_hlasy, pred_mandaty, pred_kandidati, spolehlivost_txt = vypocitej_predikce(hlasy_dict, ucast_render, data_live["vsechni_kandidati"])
        df_strany_render["Mandáty (predikce 100%)"] = df_strany_render["Kandidátní listina"].map(pred_mandaty)

        zvoleni_list = data_live["zvoleni_kandidati"]
    else:
        df_strany_render, zvoleni_list, ucast_render, spolehlivost_txt = None, [], None, "Čeká se na data"

# DETEKCE NOVÉHO MANDÁTU PRO SPMD
current_spmd_m = mandates_calc.get("SDRUŽENÍ PRO MĚSTO DOMAŽLICE", 0) if 'mandates_calc' in locals() else 0
if current_spmd_m > st.session_state["last_spmd_mandates"] and st.session_state["last_spmd_mandates"] > 0:
    st.session_state["show_shot_modal"] = True
st.session_state["last_spmd_mandates"] = current_spmd_m

# PŘIPOMÍNAČ JÍDLA
now_ts = time.time()
if "last_food_time" not in st.session_state: st.session_state["last_food_time"] = now_ts

if (now_ts - st.session_state["last_food_time"]) > 1800 or st.session_state["trigger_food_now"]:
    st.markdown("""
    <div class="food-modal">
        <h2 style="margin:0; font-size: 1.8rem; font-weight:800;">🍕 VOLEBNÍ ŠTÁB: ČAS NA JÍDLO! 🍔</h2>
        <p style="margin: 8px 0 0 0; font-size: 1.1rem;">Nezapomínejte jíst a doplňovat energii! Ať ta sobotní noc stojí za to!</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Pochopeno, doplňujeme zásoby! 🍖"):
        st.session_state["last_food_time"] = now_ts
        st.session_state["trigger_food_now"] = False
        st.rerun()

# POP-UP OVERLAY S ROZMAZANÝM POZADÍM
if st.session_state.get("show_shot_modal", False):
    st.balloons()
    prehrat_oslavny_zvuk()

    st.markdown(f"""
    <div class="blur-overlay" id="celebrationOverlay">
        <div class="celebration-card">
            <h1 style="font-size: 3rem; margin: 0; font-weight: 900; text-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                 NOVÝ MANDÁT JE DOMA!
            </h1>
            <p style="font-size: 1.8rem; margin: 20px 0; font-weight: 800; color: #fef08a;">
                Sdružení pro město Domažlice právě získalo <span style="font-size: 2.2rem; color: #ffffff;">{current_spmd_m}. mandát</span>!
            </p>
            <div style="font-size: 1.4rem; background: rgba(0,0,0,0.25); padding: 16px 24px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.2);">
                <b>POVINNOST ŠTÁBU:</b> Všichni povinně RUNDU PANÁKŮ na oslavu! 🥂🍾
            </div>
            <div class="shot-timer-bar"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    time.sleep(5)
    st.session_state["show_shot_modal"] = False
    st.rerun()

# HORNÍ ROBUSTNÍ SOUHRN MĚSTA & PREDIKCE
if ucast_render:
    ts_now = datetime.now().strftime("%H:%M:%S")
    status_txt = "SIMULACE 2026" if st.session_state["is_simulation_active"] else f"LIVE ({ts_now})"
    
    st.markdown(f"""
    <div class="robust-summary-box">
        <div class="summary-title">
            <span>🏛️ DOMAŽLICE — VOLEBNÍ VÝSLEDKY A PREDIKCE (21 MANDÁTŮ)</span>
            <span style="font-size: 0.95rem; background: #0284c7; padding: 2px 10px; border-radius: 6px;">{status_txt}</span>
        </div>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-label">Sečteno Okrsků</div>
                <div class="summary-value">{ucast_render['okrsky_zprac']} / {ucast_render['okrsky_celkem']} ({ucast_render['okrsky_proc']:.1f}%)</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Volební Účast</div>
                <div class="summary-value" style="color: #4ade80;">{ucast_render['ucast_proc']:.2f}%</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Platné Hlasy</div>
                <div class="summary-value" style="color: #f59e0b;">{ucast_render['platne_hlasy']:,}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Spolehlivost Predikce</div>
                <div class="summary-value" style="font-size: 1.1rem; color: #facc15;">{spolehlivost_txt}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">SPMD Mandáty (Predikce)</div>
                <div class="summary-value" style="color: #38bdf8;">{pred_mandaty.get('SDRUŽENÍ PRO MĚSTO DOMAŽLICE', 0)} m.</div>
            </div>
        </div>
    </div>
    """.replace(',', ' '), unsafe_allow_html=True)

# ZÁLOŽKY
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 VÝSLEDKY & PREDIKCE", 
    "🤝 KOALIČNÍ KALKULÁTOR", 
    "📜 KOMPLETNÍ KANDIDÁTKY 2026",
    "🗺️ DETAIL OKRSKŮ"
])

with tab1:
    if df_strany_render is not None:
        col_strany, col_zastupitele = st.columns([1.2, 1.8])

        # TABULKA STRAN S PREDIKCÍ
        with col_strany:
            st.markdown("<h4 style='margin:0 0 8px 0; font-weight:800;'>📊 Výsledky a predikce podle stran</h4>", unsafe_allow_html=True)
            
            def trend_mandatu(row):
                act = row["Mandáty (aktuální)"]
                prd = row["Mandáty (predikce 100%)"]
                diff = prd - act
                if diff > 0: return f"{prd} m. (↗️ +{diff})"
                elif diff < 0: return f"{prd} m. (↘️ {diff})"
                else: return f"{prd} m. (➡️ 0)"

            df_strany_render["Predikce 100%"] = df_strany_render.apply(trend_mandatu, axis=1)

            st.dataframe(
                df_strany_render[["Kandidátní listina", "Celkem hlasů", "Podíl (%)", "Mandáty (aktuální)", "Predikce 100%"]].sort_values(by="Celkem hlasů", ascending=False), 
                use_container_width=True, 
                hide_index=True,
                height=520
            )

        # MŘÍŽKA ZASTUPITELŮ S PREDIKCÍ PREFERENČNÍCH HLASŮ
        with col_zastupitele:
            st.markdown("<h4 style='margin:0 0 8px 0; font-weight:800;'>👥 Zvolení a predikovaní zastupitelé (21 křesel)</h4>", unsafe_allow_html=True)
            if zvoleni_list:
                df_zvoleni = pd.DataFrame(zvoleni_list).sort_values(by="Preferenční hlasy", ascending=False)
                zastupitelie_list = df_zvoleni.to_dict('records')
                
                pred_map = {k["Jméno a příjmení"]: k.get("Preferenční hlasy (predikce)", k["Preferenční hlasy"]) for k in pred_kandidati} if 'pred_kandidati' in locals() else {}

                grid_cols = st.columns(3)
                
                for idx, rep in enumerate(zastupitelie_list[:21]):
                    col_target = grid_cols[idx % 3]
                    jmeno = rep["Jméno a příjmení"]
                    strana = rep["Kandidátní listina"]
                    hlasy = rep["Preferenční hlasy"]
                    pred_hlasy_val = pred_map.get(jmeno, hlasy)
                    
                    party_color = get_party_color(strana)
                    bg_rgba = hex_to_rgba(party_color, alpha=0.18)

                    card_code = f"""
                    <div class="rep-card-box" style="background-color: {bg_rgba}; border-left: 20px solid {party_color};">
                        <div>
                            <div class="rep-name" title="{jmeno}">#{idx+1} {jmeno}</div>
                            <div class="rep-party" title="{strana}">{strana}</div>
                        </div>
                        <div class="rep-foot">
                            <span class="rep-votes">{hlasy:,} h.</span>
                            <span class="rep-pred-votes" title="Očekávaný výsledek při 100% sečtení">🔮 ~{pred_hlasy_val:,} h.</span>
                        </div>
                    </div>
                    """.replace(',', ' ')
                    
                    col_target.markdown(card_code, unsafe_allow_html=True)

with tab2:
    if df_strany_render is not None:
        vsechny_strany = list(df_strany_render["Kandidátní listina"].unique())
        
        c1, c2 = st.columns(2)
        with c1: zakazane_strany = st.multiselect("🚫 Vyloučit z koalice (Red-line):", vsechny_strany, default=[])
        with c2: povinne_strany = st.multiselect("🔒 Nutná součást koalice:", vsechny_strany, default=[])

        koalice = najdi_koalice(mandates_calc, min_kresel=11, zakazane=zakazane_strany, povinne=povinne_strany)
        
        if not koalice:
            st.warning("Při zvolených podmínkách neexistuje žádná většina 11+ mandátů!")
        else:
            for combo, kresla, status_txt, status_class in koalice:
                party_badges = [f'<span style="background-color: {get_party_color(s)}; color: white; padding: 4px 10px; border-radius: 6px; margin-right: 6px; font-weight: bold; font-size: 0.9rem; display: inline-block; margin-bottom: 4px;">{s}: {mandates_calc[s]} m.</span>' for s in combo]
                
                st.markdown(f"""
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 1.1rem; font-weight: 800; color: #ffffff;">Většina {kresla} mandátů</span>
                        <span class="{status_class}">{status_txt}</span>
                    </div>
                    <div>{" ".join(party_badges)}</div>
                </div>
                """, unsafe_allow_html=True)

with tab3:
    st.subheader("📜 Kompletní kandidátní listiny všech stran pro rok 2026")
    if df_kandidatky_2026 is not None:
        p_col = 'Kandidátní listina.název'
        f1, f2 = st.columns(2)
        with f1: vybrana_kandidatka = st.selectbox("Vyberte kandidátní listinu:", ["Všechny"] + list(df_kandidatky_2026[p_col].unique()))
        with f2: search_q = st.text_input("🔍 Vyhledat kandidáta podle jména:", "")
        
        df_s = df_kandidatky_2026.copy()
        if vybrana_kandidatka != "Všechny": 
            df_s = df_s[df_s[p_col] == vybrana_kandidatka]
        if search_q: 
            df_s = df_s[df_s['Kandidát.příjmení, jméno, tituly'].str.contains(search_q, case=False, na=False, regex=False)]
            
        st.dataframe(
            df_s[['Kandidátní listina.číslo', p_col, 'Kandidát.poř. číslo', 'Kandidát.příjmení, jméno, tituly', 'Kandidát.věk', 'Navrhující strana', 'Politická příslušnost', 'Povolání', 'Bydliště']], 
            use_container_width=True, 
            hide_index=True,
            height=450
        )

with tab4:
    if ucast_render:
        st.write(f"Sečteno **{ucast_render['okrsky_zprac']} z {ucast_render['okrsky_celkem']} okrsků** ({ucast_render['okrsky_proc']:.1f} %).")
        st.progress(ucast_render['okrsky_proc'] / 100.0)