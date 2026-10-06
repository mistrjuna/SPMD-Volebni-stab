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
    initial_sidebar_state="expanded"
)

REFRESH_INTERVAL = 60

# --- PŘESNÉ BAREVNÉ SCHÉMA STRAN ---
PARTY_COLORS = {
    "STRANA PRO DOMAŽLICE": "#f8ea4e",
    "Pro Domažlice, KDU-ČSL a nezávislí": "#f8ea4e",
    "VAŠE DOMAŽLICE": "#03abf4",
    "Stačilo! (KSČM a nezávislí)": "#dc2626",
    "ANO 2011 a nezávislí": "#b1e3da",
    "ANO 2011 s podporou nezávislých": "#b1e3da",
    "Česká pirátská strana": "#000000",
    "Občanská demokratická strana": "#004494",
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

# --- OPRAVA ODSAZENÍ (PADDING-TOP) OD HORNÍ LIŠTY APP ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    /* Odsazení od horního okraje Streamlit lišty (Deploy / Menu) */
    .block-container {
        padding-top: 4.5rem !important;
        padding-bottom: 2rem !important;
    }

    .cmd-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 14px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .cmd-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .status-online {
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid #22c55e;
        color: #86efac;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: 'JetBrains Mono', monospace;
    }
    .status-sim {
        background: rgba(248, 234, 78, 0.2);
        border: 1px solid #f8ea4e;
        color: #fef08a;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: 'JetBrains Mono', monospace;
    }
    .status-dot-green {
        width: 8px;
        height: 8px;
        background-color: #22c55e;
        border-radius: 50%;
        box-shadow: 0 0 8px #22c55e;
    }
    .status-dot-yellow {
        width: 8px;
        height: 8px;
        background-color: #f8ea4e;
        border-radius: 50%;
        box-shadow: 0 0 8px #f8ea4e;
    }

    .rep-card-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 8px;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .rep-name {
        font-size: 0.88rem;
        font-weight: 800;
        color: #f8fafc;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .rep-party {
        font-size: 0.72rem;
        font-weight: 600;
        color: #94a3b8;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .rep-foot {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 6px;
        font-family: 'JetBrains Mono', monospace;
    }
    .rep-votes {
        font-size: 0.8rem;
        font-weight: 700;
        color: #38bdf8;
    }

    .trend-pill {
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
    }
    .trend-up { background: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid #22c55e; }
    .trend-down { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; }
    .trend-same { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid #64748b; }
    .trend-new { background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid #38bdf8; }

    .badge-krehka { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; }
    .badge-bezpecna { background: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid #22c55e; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; }
    .badge-dominantni { background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid #38bdf8; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; }

    .shot-modal {
        background: linear-gradient(135deg, #026a7f 0%, #0284c7 100%);
        border: 2px solid #38bdf8;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 0 30px rgba(2, 106, 127, 0.6);
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

# --- VESTAVĚNÁ KOMPLETNÍ DATA KANDIDÁTEK 2026 (BEZ POTŘEBY SOUTORU CSV) ---
@st.cache_data
def nacti_kandidatky_2026_built_in():
    try:
        # Zkouška z CSV
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
        # VESTAVĚNÉ KLÍČOVÉ KANDIDÁTKY ZE SOUBORU
        built_in_kands = [
            # VAŠE DOMAŽLICE
            {"Kandidátní listina.číslo": 1, "Kandidátní listina.název": "VAŠE DOMAŽLICE", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Krutina Viktor Ing.", "Kandidát.věk": 48, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "1. místostarosta města Domažlice", "Bydliště": "Dolejší Předměstí"},
            {"Kandidátní listina.číslo": 1, "Kandidátní listina.název": "VAŠE DOMAŽLICE", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Štangl Jiří", "Kandidát.věk": 48, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "hlavní mistr", "Bydliště": "Dolejší Předměstí"},
            {"Kandidátní listina.číslo": 1, "Kandidátní listina.název": "VAŠE DOMAŽLICE", "Kandidát.poř. číslo": 3, "Kandidát.příjmení, jméno, tituly": "Špoták Rudolf", "Kandidát.věk": 43, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "emeritní hejtman Plzeňského kraje", "Bydliště": "Bezděkovské Předměstí"},

            # PRO DOMAŽLICE
            {"Kandidátní listina.číslo": 4, "Kandidátní listina.název": "Pro Domažlice, KDU-ČSL a nezávislí", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Bc. Stanislav Antoš", "Kandidát.věk": 59, "Navrhující strana": "KDU-ČSL", "Politická příslušnost": "KDU-ČSL", "Povolání": "starosta města Domažlice", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 4, "Kandidátní listina.název": "Pro Domažlice, KDU-ČSL a nezávislí", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Vorlíček Marek MgA.", "Kandidát.věk": 47, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "varhanář, sbormistr, radní", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 4, "Kandidátní listina.název": "Pro Domažlice, KDU-ČSL a nezávislí", "Kandidát.poř. číslo": 3, "Kandidát.příjmení, jméno, tituly": "Kadlec Ivo MUDr.", "Kandidát.věk": 71, "Navrhující strana": "KDU-ČSL", "Politická příslušnost": "BEZPP", "Povolání": "zubní lékař", "Bydliště": "Domažlice"},

            # ANO 2011
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Wiesner Radek, Ing.", "Kandidát.věk": 47, "Navrhující strana": "ANO", "Politická příslušnost": "ANO", "Povolání": "konstruktér, manažer výroby", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Pauler David, Mgr.", "Kandidát.věk": 45, "Navrhující strana": "ANO", "Politická příslušnost": "ANO", "Povolání": "pedagog, podnikatel", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 3, "Kandidát.příjmení, jméno, tituly": "Piták Martin, Mgr.", "Kandidát.věk": 41, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "manažer", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 4, "Kandidát.příjmení, jméno, tituly": "Bor David", "Kandidát.věk": 44, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "OSVČ", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 3, "Kandidátní listina.název": "ANO 2011 a nezávislí", "Kandidát.poř. číslo": 5, "Kandidát.příjmení, jméno, tituly": "Látka Jan", "Kandidát.věk": 72, "Navrhující strana": "ANO", "Politická příslušnost": "ANO", "Povolání": "senátor", "Bydliště": "Domažlice"},

            # SPMD
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Mgr. Kamil Jindřich", "Kandidát.věk": 53, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "hudebník, učitel", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Josef Kuneš", "Kandidát.věk": 47, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "ředitel ZUŠ", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 3, "Kandidát.příjmení, jméno, tituly": "Mgr. Ivan Rybár", "Kandidát.věk": 60, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "ředitel základní školy Domažlice", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 4, "Kandidát.příjmení, jméno, tituly": "Novák Zdeněk JUDr.", "Kandidát.věk": 74, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "emeritní starosta, důchodce", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 7, "Kandidátní listina.název": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát.poř. číslo": 5, "Kandidát.příjmení, jméno, tituly": "Ing. Zbyněk Wolf", "Kandidát.věk": 52, "Navrhující strana": "STAN", "Politická příslušnost": "BEZPP", "Povolání": "projektant", "Bydliště": "Domažlice"},

            # ODS
            {"Kandidátní listina.číslo": 6, "Kandidátní listina.název": "Občanská demokratická strana", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Faschingbauer Pavel, Ing.", "Kandidát.věk": 53, "Navrhující strana": "ODS", "Politická příslušnost": "ODS", "Povolání": "ekonom", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 6, "Kandidátní listina.název": "Občanská demokratická strana", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Mgr. Jakub Faschingbauer", "Kandidát.věk": 33, "Navrhující strana": "ODS", "Politická příslušnost": "BEZPP", "Povolání": "lékárník", "Bydliště": "Domažlice"},

            # ŽIJEME DOMAŽLICE
            {"Kandidátní listina.číslo": 8, "Kandidátní listina.název": "ŽIJEME DOMAŽLICE - VÝZVA PRO NOVÝ SMĚR MĚSTA", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Hradecká Hana Mgr. et Mgr.", "Kandidát.věk": 59, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "středoškolská učitelka VOŠ, OA a SZŠ Domažlice", "Bydliště": "Domažlice"},
            {"Kandidátní listina.číslo": 8, "Kandidátní listina.název": "ŽIJEME DOMAŽLICE - VÝZVA PRO NOVÝ SMĚR MĚSTA", "Kandidát.poř. číslo": 2, "Kandidát.příjmení, jméno, tituly": "Piták Luboš Mgr.", "Kandidát.věk": 62, "Navrhující strana": "NK", "Politická příslušnost": "BEZPP", "Povolání": "OSVČ, právník", "Bydliště": "Domažlice"},

            # SPD
            {"Kandidátní listina.číslo": 9, "Kandidátní listina.název": "Svoboda a přímá demokracie (SPD)", "Kandidát.poř. číslo": 1, "Kandidát.příjmení, jméno, tituly": "Obdržálek Michal	", "Kandidát.věk": 36, "Navrhující strana": "SPD", "Politická příslušnost": "SPD", "Povolání": "živnostník v pohostinství, zastupitel města", "Bydliště": "Domažlice"},

            # PIRÁTI
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

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ Simulační Centrum 2026")

if "is_simulation_active" not in st.session_state:
    st.session_state["is_simulation_active"] = False

if "simulated_bonus_mandate" not in st.session_state:
    st.session_state["simulated_bonus_mandate"] = 0

if "trigger_food_now" not in st.session_state:
    st.session_state["trigger_food_now"] = False

if "show_shot_modal" not in st.session_state:
    st.session_state["show_shot_modal"] = False

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

PAST_PARTY_MAP = {
    "ANO 2011 a nezávislí": "ANO 2011 s podporou nezávislých",
    "Pro Domažlice, KDU-ČSL a nezávislí": "Vždy Domažlice - KDU-ČSL a nezávislí",
    "Stačilo! (KSČM a nezávislí)": "Komunistická strana Čech a Moravy",
    "STRANA PRO DOMAŽLICE": "Vždy Domažlice - KDU-ČSL a nezávislí"
}

# SESTAVENÍ SIMULAČNÍHO MODELU PODLE ODKAZOVANÉ TABULKY PREDIKCÍ
if st.session_state["is_simulation_active"]:
    sim_votes = {
        "SDRUŽENÍ PRO MĚSTO DOMAŽLICE": 14700,             # 21.1% -> 5 mandátů
        "ANO 2011 a nezávislí": 14700,                    # 21.1% -> 5 mandátů
        "Pro Domažlice, KDU-ČSL a nezávislí": 9500,        # 13.7% -> 3 mandáty
        "Občanská demokratická strana": 7200,              # 10.4% -> 2 mandáty
        "VAŠE DOMAŽLICE": 6300,                            # 9.1%  -> 2 mandáty
        "ŽIJEME DOMAŽLICE - VÝZVA PRO NOVÝ SMĚR MĚSTA": 5600,# 8.1%  -> 2 mandáty
        "Svoboda a přímá demokracie (SPD)": 4900,          # 7.1%  -> 1 mandát
        "Česká pirátská strana": 3800,                     # 5.5%  -> 1 mandát
        "Stačilo! (KSČM a nezávislí)": 2800                # 4.0%  -> 0 mandátů
    }
    
    mandates_calc, pct_calc = vypocitej_mandaty(sim_votes)
    if "SDRUŽENÍ PRO MĚSTO DOMAŽLICE" in mandates_calc:
        mandates_calc["SDRUŽENÍ PRO MĚSTO DOMAŽLICE"] += st.session_state["simulated_bonus_mandate"]
        
    df_strany_render = pd.DataFrame([
        {"Kandidátní listina": k, "Celkem hlasů": v, "Podíl (%)": pct_calc[k], "Mandáty": mandates_calc[k]}
        for k, v in sim_votes.items()
    ])
    
    def srovnej_mandaty_sim(row):
        nazev, aktualni = row["Kandidátní listina"], row["Mandáty"]
        past_name = PAST_PARTY_MAP.get(nazev, nazev)
        if past_name in past_mandates:
            rozdil = aktualni - past_mandates[past_name]
            if rozdil > 0: return f"🟢 +{rozdil} m."
            elif rozdil < 0: return f"🔴 {rozdil} m."
            else: return "⚪ 0 m."
        return "🆕 Nová"

    df_strany_render["Srovnání (2022)"] = df_strany_render.apply(srovnej_mandaty_sim, axis=1)

    # GENERUJEME ZVOLENÉ ZASTUPITELE Z VESTAVĚNÉHO SEZNAMU
    zvoleni_list = []
    vsechni_list = []
    
    if df_kandidatky_2026 is not None:
        p_col = 'Kandidátní listina.název'
        n_col = 'Kandidát.příjmení, jméno, tituly'
        num_col = 'Kandidát.poř. číslo'
        
        for party, m_count in mandates_calc.items():
            if m_count <= 0: continue
            
            # Bezpečné hledání bez regexu
            party_kands = df_kandidatky_2026[
                df_kandidatky_2026[p_col].str.contains(party[:10], case=False, na=False, regex=False)
            ].sort_values(by=num_col)
            
            if party_kands.empty:
                for i in range(1, m_count + 1):
                    cand_obj = {
                        "Poř.": i,
                        "Jméno a příjmení": f"Kandidát #{i} ({party})",
                        "Kandidátní listina": party,
                        "Preferenční hlasy": int(sim_votes[party] / 15) - i * 10,
                        "Podíl hlasů (%)": 5.0,
                        "Zvolen": True,
                        "Status": "✅ Získal mandát"
                    }
                    zvoleni_list.append(cand_obj)
            else:
                for idx, (_, row) in enumerate(party_kands.iterrows()):
                    jmeno = row[n_col]
                    poradi = row[num_col]
                    is_elected = (idx < m_count)
                    pref_votes = max(100, int(sim_votes[party] / 21) + (21 - poradi) * 35)
                    
                    cand_obj = {
                        "Poř.": poradi,
                        "Jméno a příjmení": jmeno,
                        "Kandidátní listina": party,
                        "Preferenční hlasy": pref_votes,
                        "Podíl hlasů (%)": round((pref_votes / sim_votes[party]) * 100, 2),
                        "Zvolen": is_elected
                    }
                    vsechni_list.append(cand_obj)
                    if is_elected:
                        cand_obj["Status"] = "✅ Získal mandát"
                        zvoleni_list.append(cand_obj)
                    
    ucast_render = {
        "okrsky_celkem": 12, "okrsky_zprac": 12, "okrsky_proc": 100.0,
        "zapsani_volici": 8214, "vydane_obalky": 3777, "platne_hlasy": sum(sim_votes.values()),
        "ucast_proc": 45.98
    }

else:
    if data_live and data_live["strany"]:
        df_strany_render = pd.DataFrame(data_live["strany"])
        hlasy_dict = dict(zip(df_strany_render["Kandidátní listina"], df_strany_render["Celkem hlasů"]))
        mandates_calc, pct_calc = vypocitej_mandaty(hlasy_dict)
        
        if "SDRUŽENÍ PRO MĚSTO DOMAŽLICE" in mandates_calc:
            mandates_calc["SDRUŽENÍ PRO MĚSTO DOMAŽLICE"] += st.session_state["simulated_bonus_mandate"]
            
        df_strany_render["Mandáty"] = df_strany_render["Kandidátní listina"].map(mandates_calc)
        
        def srovnej_mandaty_live(row):
            nazev, aktualni = row["Kandidátní listina"], row["Mandáty"]
            if nazev in past_mandates:
                rozdil = aktualni - past_mandates[nazev]
                if rozdil > 0: return f"🟢 +{rozdil} m."
                elif rozdil < 0: return f"🔴 {rozdil} m."
                else: return "⚪ 0 m."
            return "🆕 Nová"

        df_strany_render["Srovnání (2022)"] = df_strany_render.apply(srovnej_mandaty_live, axis=1)

        zvoleni_list = data_live["zvoleni_kandidati"]
        vsechni_list = data_live["vsechni_kandidati"]
        ucast_render = data_live["ucast"]
    else:
        df_strany_render, zvoleni_list, vsechni_list, ucast_render = None, [], [], None

# --- PŘIPOMÍNAČ JÍDLA ---
now_ts = time.time()
if "last_food_time" not in st.session_state:
    st.session_state["last_food_time"] = now_ts

if (now_ts - st.session_state["last_food_time"]) > 1800 or st.session_state["trigger_food_now"]:
    st.markdown("""
    <div class="food-modal">
        <h2 style="margin:0; font-size: 1.8rem; font-weight:800;">🍕 VOLEBNÍ ŠTÁB: ČAS NA JÍDLO! 🍔</h2>
        <p style="margin: 8px 0 0 0; font-size: 1.1rem;">
            Nezapomínejte jíst a doplňovat energii! Ať ta sobotní noc stojí za to a vydržíte v plné síle až do konečných výsledků!
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Pochopeno, doplňujeme zásoby! 🍖"):
        st.session_state["last_food_time"] = now_ts
        st.session_state["trigger_food_now"] = False
        st.rerun()

# --- MODAL PRO OSLAVU MANDÁTU ---
if st.session_state.get("show_shot_modal", False):
    st.balloons()
    prehrat_oslavny_zvuk()
    spmd_m = mandates_calc.get("SDRUŽENÍ PRO MĚSTO DOMAŽLICE", 0)
    st.markdown(f"""
    <div class="shot-modal">
        <h1 style="font-size: 2.2rem; margin: 0; font-weight: 800;">🥃 DALŠÍ MANDÁT JE DOMA! 🥃</h1>
        <p style="font-size: 1.3rem; margin: 10px 0 15px 0;">
            Sdružení pro město Domažlice právě získalo <b>{spmd_m}. mandát</b>! <br>
            <b>POVINNOST ŠTÁBU: Všichni povinně RUNDU PANÁKŮ na oslavu! 🥂🍾</b>
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Zavřít a pokračovat v oslavě 🥂"):
        st.session_state["show_shot_modal"] = False
        st.rerun()

# --- HEADER APP ---
ts_now = datetime.now().strftime("%H:%M:%S")
if st.session_state["is_simulation_active"]:
    status_html = f'<span class="status-sim"><span class="status-dot-yellow"></span> SIMULAČNÍ REŽIM (Predikce 2026)</span>'
else:
    status_html = f'<span class="status-online"><span class="status-dot-green"></span> ONLINE ({ts_now})</span>'

st.markdown(f"""
<div class="cmd-header">
    <div class="cmd-title">
        🏛️ SPMD — Řídicí Centrum Volebního Štábu Domažlice
        {status_html}
    </div>
    <div style="color: #38bdf8; font-weight: 700;">DOMAŽLICE (21 MANDÁTŮ)</div>
</div>
""", unsafe_allow_html=True)

if ucast_render:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sečtenost okrsků", f"{ucast_render['okrsky_zprac']} / {ucast_render['okrsky_celkem']}", f"{ucast_render['okrsky_proc']:.1f} %")
    m2.metric("Volební účast", f"{ucast_render['ucast_proc']:.2f} %")
    m3.metric("Zapsaní voliči", f"{ucast_render['zapsani_volici']:,}".replace(',', ' '))
    m4.metric("Platné hlasy", f"{ucast_render['platne_hlasy']:,}".replace(',', ' '))

# --- ZÁLOŽKY ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 COMMAND CENTER: Výsledky & Zastupitelé", 
    "🤝 KOALIČNÍ KALKULÁTOR & RED-LINES", 
    "📜 KOMPLETNÍ KANDIDÁTKY STRAN 2026",
    "🗺️ DETAIL SČÍTÁNÍ OKRSKŮ"
])

# ==========================================
# COMMAND CENTER: VÝSLEDKY & ZASTUPITELÉ
# ==========================================
with tab1:
    if df_strany_render is not None:
        col_strany, col_zastupitele = st.columns([1.1, 1.9])

        with col_strany:
            st.markdown("##### 📈 Výsledky stran & d'Hondtovy mandáty")
            
            st.dataframe(
                df_strany_render[["Kandidátní listina", "Celkem hlasů", "Podíl (%)", "Mandáty", "Srovnání (2022)"]].sort_values(by="Celkem hlasů", ascending=False), 
                use_container_width=True, 
                hide_index=True,
                height=340
            )

            st.markdown("##### 📊 Grafický poměr sil v zastupitelstvu")
            df_chart = df_strany_render[df_strany_render["Mandáty"] > 0].set_index("Kandidátní listina")[["Mandáty"]]
            st.bar_chart(df_chart, horizontal=True, color="#026a7f")

        with col_zastupitele:
            st.markdown("##### 👥 Zvolení zastupitelé Domažlic (21 mandátů)")
            
            if zvoleni_list:
                df_zvoleni = pd.DataFrame(zvoleni_list).sort_values(by="Preferenční hlasy", ascending=False)
                zastupitelie_list = df_zvoleni.to_dict('records')
                
                grid_cols = st.columns(3)
                
                for idx, rep in enumerate(zastupitelie_list[:21]):
                    col_target = grid_cols[idx % 3]
                    jmeno = rep["Jméno a příjmení"]
                    strana = rep["Kandidátní listina"]
                    hlasy = rep["Preferenční hlasy"]
                    border_color = get_party_color(strana)

                    if jmeno in past_votes_kand:
                        diff = hlasy - past_votes_kand[jmeno]
                        if diff > 0:
                            trend_badge = f'<span class="trend-pill trend-up">🟢 +{diff:,} h.</span>'
                        elif diff < 0:
                            trend_badge = f'<span class="trend-pill trend-down">🔴 {diff:,} h.</span>'
                        else:
                            trend_badge = '<span class="trend-pill trend-same">⚪ 0 h.</span>'
                    else:
                        trend_badge = '<span class="trend-pill trend-new">🆕 NEW</span>'

                    card_code = f"""
                    <div class="rep-card-box" style="border-left: 5px solid {border_color};">
                        <div>
                            <div class="rep-name" title="{jmeno}">#{idx+1} {jmeno}</div>
                            <div class="rep-party" title="{strana}">{strana}</div>
                        </div>
                        <div class="rep-foot">
                            <span class="rep-votes">{hlasy:,} h.</span>
                            {trend_badge}
                        </div>
                    </div>
                    """.replace(',', ' ')
                    
                    col_target.markdown(card_code, unsafe_allow_html=True)

# ==========================================
# KARTA 2: KOALIČNÍ KALKULÁTOR
# ==========================================
with tab2:
    st.subheader("🤝 Koaliční kalkulátor a varianty většiny (≥ 11 křesel)")
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
                party_badges = [f'<span style="background-color: {get_party_color(s)}; color: white; padding: 4px 10px; border-radius: 6px; margin-right: 6px; font-weight: bold; font-size: 0.85rem; display: inline-block; margin-bottom: 4px;">{s}: {mandates_calc[s]} m.</span>' for s in combo]
                
                st.markdown(f"""
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 14px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 1.1rem; font-weight: 800; color: #ffffff;">Většina {kresla} mandátů</span>
                        <span class="{status_class}">{status_txt}</span>
                    </div>
                    <div>{" ".join(party_badges)}</div>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# KARTA 3: KOMPLETNÍ KANDIDÁTKY STRAN
# ==========================================
with tab3:
    st.subheader("📜 Kompletní kandidátní listiny všech 9 stran pro rok 2026")
    
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
            hide_index=True
        )

# ==========================================
# KARTA 4: DETAIL OKRSKŮ
# ==========================================
with tab4:
    st.subheader("🗺️ Detailní sčítání po domažlických okrscích")
    if ucast_render:
        st.write(f"Sečteno **{ucast_render['okrsky_zprac']} z {ucast_render['okrsky_celkem']} okrsků** ({ucast_render['okrsky_proc']:.1f} %).")
        st.progress(ucast_render['okrsky_proc'] / 100.0)
