import streamlit as st
import pandas as pd
import urllib.request
import xml.etree.ElementTree as ET
from itertools import combinations

st.set_page_config(
    page_title="SPMD — Volební Štáb LIVE Domažlice", 
    layout="wide", 
    page_icon="🏛️"
)

# --- VYUŽITÍ ZNAČKOVÝCH BAREV Z LOGA SPMD ---
SPMD_BLUE = "#084c61"       # Hluboká petrolejově modrá z pozadí loga
SPMD_TEAL = "#006b88"       # Jasnější petrolejový akcent
SPMD_LIGHT_BG = "#f0f4f7"   # Světlé neutrální pozadí pro karty
SPMD_DARK_TEXT = "#0d2b35"  # Tmavý text pro kontrast

PARTY_COLORS = {
    "SDRUŽENÍ PRO MĚSTO DOMAŽLICE": {"bg": "#084c61", "text": "#ffffff"},
    "ANO 2011 s podporou nezávislých": {"bg": "#2b90b8", "text": "#ffffff"},
    "Vždy Domažlice - KDU-ČSL a nezávislí": {"bg": "#d9a036", "text": "#ffffff"},
    "Občanská demokratická strana": {"bg": "#002b49", "text": "#ffffff"},
    "Svoboda a přímá demokracie (SPD)": {"bg": "#59473c", "text": "#ffffff"},
    "Česká pirátská strana": {"bg": "#1c2126", "text": "#ffffff"},
    "Domažlice pro všechny": {"bg": "#238073", "text": "#ffffff"},
    "Komunistická strana Čech a Moravy": {"bg": "#b82835", "text": "#ffffff"},
    "Česká strana sociálně demokratická": {"bg": "#d96b27", "text": "#ffffff"},
    "Domažlice - náš domov": {"bg": "#7a9a95", "text": "#ffffff"}
}

# --- MODERNOST A STYLING APLIKACE (CSS) ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: #f7fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    
    .spmd-header {{
        background: linear-gradient(135deg, {SPMD_BLUE} 0%, #032b38 100%);
        color: white;
        padding: 24px 32px;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(8, 76, 97, 0.15);
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .spmd-title {{
        font-size: 2.1em;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }}
    .spmd-subtitle {{
        font-size: 1.05em;
        opacity: 0.9;
        margin-top: 4px;
    }}
    
    .spmd-metric-card {{
        background: white;
        padding: 18px 22px;
        border-radius: 14px;
        border-left: 5px solid {SPMD_TEAL};
        box-shadow: 0 3px 10px rgba(0,0,0,0.04);
    }}
    .spmd-metric-label {{
        font-size: 0.85em;
        color: #5c7178;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .spmd-metric-val {{
        font-size: 1.7em;
        font-weight: 800;
        color: {SPMD_DARK_TEXT};
        margin: 4px 0;
    }}
    .spmd-metric-sub {{
        font-size: 0.85em;
        color: {SPMD_TEAL};
        font-weight: 600;
    }}
    
    .badge-krehka {{ background-color: #ffebe9; color: #b71c1c; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.85em; }}
    .badge-bezpecna {{ background-color: #e8f5e9; color: #1b5e20; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.85em; }}
    .badge-dominantni {{ background-color: #e0f7fa; color: #006064; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.85em; }}
    
    .stDataFrame {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }}
</style>
""", unsafe_allow_html=True)

# HLAVIČKA V DESIGNU LOGA SPMD
st.markdown(f"""
<div class="spmd-header">
    <div>
        <div class="spmd-title">🏛️ SPMD — Řídicí Centrum Volebního Štábu</div>
        <div class="spmd-subtitle">Domažlice 2026 | Živý monitoring sčítání, přepočet d'Hondtových mandátů a analýza většin</div>
    </div>
    <div style="text-align: right; font-weight: 800; font-size: 1.8em; letter-spacing: 2px;">
        SPMD
    </div>
</div>
""", unsafe_allow_html=True)

# --- UNIVERZÁLNÍ NAČÍTÁNÍ DATA Z ČSÚ XML ---
def nacti_kompletni_csu_data(url, kod_zastup="553425"):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        raw_bytes = urllib.request.urlopen(req, timeout=12).read()
        
        root = ET.fromstring(raw_bytes)
        
        target_obec = None
        for elem in root.iter():
            if elem.attrib.get('KODZASTUP') == kod_zastup:
                target_obec = elem
                break
                
        if target_obec is None:
            return None, f"V XML nebyl nalezen uzel s KODZASTUP='{kod_zastup}'."

        strany_list = []
        zvoleni_kandidati_list = []
        vsechni_kandidati_list = []
        
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
                        titul_pred = k_attr.get('TITULPRED', '')
                        titul_za = k_attr.get('TITULZA', '')
                        jmeno = k_attr.get('JMENO', '')
                        prijmeni = k_attr.get('PRIJMENI', '')
                        
                        celkovo_jmeno = f"{titul_pred} {jmeno} {prijmeni} {titul_za}".strip()
                        poradi = int(k_attr.get('PORADOVE_CISLO', 0))
                        hlasy_kand = int(k_attr.get('HLASY', 0))
                        proc_kand = float(k_attr.get('HLASY_PROC', 0.0))

                        is_zvolen = (k_tag == 'ZASTUPITEL')

                        cand_obj = {
                            "Poř.": poradi,
                            "Jméno a příjmení": celkovo_jmeno,
                            "Kandidátní listina": nazev_strany,
                            "Preferenční hlasy": hlasy_kand,
                            "Podíl hlasů (%)": proc_kand,
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
                    "odevzdane_obalky": int(u_attr.get('ODEVZDANE_OBALKY', 0)),
                    "platne_hlasy": int(u_attr.get('PLATNE_HLASY', 0)),
                    "ucast_proc": float(u_attr.get('UCAST_PROC', 0.0))
                }

        kompletni_data = {
            "strany": strany_list,
            "zvoleni_kandidati": zvoleni_kandidati_list,
            "vsechni_kandidati": vsechni_kandidati_list,
            "ucast": ucast_data
        }

        return kompletni_data, None

    except Exception as e:
        return None, f"Chyba při načítání XML: {e}"

def vypocitej_mandaty(hlasy_dict, celkem_mandatu=21, hranice_pct=5.0):
    celkem_hlasu = sum(hlasy_dict.values())
    if celkem_hlasu == 0:
        return {}, {}
    
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
            if not all(p in combo for p in povinne):
                continue
                
            kresla = sum(mandaty[s] for s in combo)
            if kresla >= min_kresel:
                is_minimal = True
                for s in combo:
                    if s not in povinne and (kresla - mandaty[s]) >= min_kresel:
                        is_minimal = False
                        break
                if is_minimal:
                    if kresla == 11:
                        status_class = "badge-krehka"
                        status_txt = "🔴 Křehká většina (11 mandátů)"
                    elif kresla in [12, 13]:
                        status_class = "badge-bezpecna"
                        status_txt = "🟢 Bezpečná většina (12–13 mandátů)"
                    else:
                        status_class = "badge-dominantni"
                        status_txt = "🔵 Svrchovaná většina (14+ mandátů)"
                    vysledky.append((combo, kresla, status_txt, status_class))
                    
    vysledky.sort(key=lambda x: (x[1], len(x[0])))
    return vysledky

# --- SIDEBAR & ZDROJE DAT ---
st.sidebar.markdown("### 📡 Datové Zdroje ČSÚ")
url_live = st.sidebar.text_input(
    "Živá URL data (Aktuální volby):", 
    value="https://volby.gov.cz/pls/kv2022/vysledky_obce_okres?datumvoleb=20220923&nuts=CZ0321"
)
url_2022 = st.sidebar.text_input(
    "URL data 2022 (Srovnávací záloha):", 
    value="https://volby.gov.cz/pls/kv2022/vysledky_obce_okres?datumvoleb=20220923&nuts=CZ0321"
)

data_live, err_live = nacti_kompletni_csu_data(url_live, kod_zastup="553425")
data_past, err_past = nacti_kompletni_csu_data(url_2022, kod_zastup="553425")

if err_live:
    st.error(err_live)
else:
    st.sidebar.success(f"✅ Živá data spojená s ČSÚ!")

past_mandates = {}
past_votes_kand = {}

if data_past:
    for s in data_past["strany"]:
        past_mandates[s["Kandidátní listina"]] = s["Mandáty ČSÚ"]
    for k in data_past["zvoleni_kandidati"]:
        past_votes_kand[k["Jméno a příjmení"]] = k["Preferenční hlasy"]

# --- STRUKTURA ZÁLOŽEK ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 DASHBOARD: Hlavní Přehled", 
    "🤝 KARTA 2: Koaliční Kalkulátor & Red-Lines", 
    "📜 KARTA 3: Kompletní Kandidátky",
    "🗺️ KARTA 4: Okrsky & Volební Účast"
])

# ==========================================
# DASHBOARD: VELKÝ HLAVNÍ PŘEHLED
# ==========================================
with tab1:
    if data_live and data_live["strany"]:
        u = data_live["ucast"]
        
        st.markdown("##### 📍 Průběh sčítání a účasti v obci")
        m1, m2, m3, m4 = st.columns(4)
        
        m1.markdown(f"""
        <div class="spmd-metric-card">
            <div class="spmd-metric-label">Sečtenost okrsků</div>
            <div class="spmd-metric-val">{u['okrsky_zprac']} / {u['okrsky_celkem']}</div>
            <div class="spmd-metric-sub">{u['okrsky_proc']:.1f} % hotovo</div>
        </div>
        """, unsafe_allow_html=True)

        m2.markdown(f"""
        <div class="spmd-metric-card">
            <div class="spmd-metric-label">Volební účast</div>
            <div class="spmd-metric-val">{u['ucast_proc']:.2f} %</div>
            <div class="spmd-metric-sub">{u['vydane_obalky']:,} obálek</div>
        </div>
        """.replace(',', ' '), unsafe_allow_html=True)

        m3.markdown(f"""
        <div class="spmd-metric-card">
            <div class="spmd-metric-label">Zapsaní voliči</div>
            <div class="spmd-metric-val">{u['zapsani_volici']:,}</div>
            <div class="spmd-metric-sub">Celkem v obci</div>
        </div>
        """.replace(',', ' '), unsafe_allow_html=True)

        m4.markdown(f"""
        <div class="spmd-metric-card">
            <div class="spmd-metric-label">Platné hlasy</div>
            <div class="spmd-metric-val">{u['platne_hlasy']:,}</div>
            <div class="spmd-metric-sub">Odevzdaných hlasů</div>
        </div>
        """.replace(',', ' '), unsafe_allow_html=True)

        st.progress(u['okrsky_proc'] / 100.0)
        st.markdown("<br>", unsafe_allow_html=True)

        col_dash_left, col_dash_right = st.columns([1.1, 1])

        # LEVÁ ČÁST DASHBOARDU: VÝSLEDKY STRAN S POROVNÁNÍM
        with col_dash_left:
            st.subheader("📈 Výsledky stran (Srovnání mandátů s minulými volbami)")
            df_strany = pd.DataFrame(data_live["strany"])
            hlasy_dict = dict(zip(df_strany["Kandidátní listina"], df_strany["Celkem hlasů"]))
            mandaty_calc, _ = vypocitej_mandaty(hlasy_dict)

            df_strany["Mandáty"] = df_strany["Kandidátní listina"].map(mandaty_calc)
            
            def srovnej_mandaty(row):
                nazev = row["Kandidátní listina"]
                aktualni = row["Mandáty"]
                if nazev in past_mandates:
                    minule = past_mandates[nazev]
                    rozdil = aktualni - minule
                    if rozdil > 0:
                        return f"🟢 +{rozdil} m. (minule {minule})"
                    elif rozdil < 0:
                        return f"🔴 {rozdil} m. (minule {minule})"
                    else:
                        return f"⚪ 0 m. (minule {minule})"
                return "🆕 Nová strana"

            df_strany["Srovnání s 2022 (Mandáty)"] = df_strany.apply(srovnej_mandaty, axis=1)

            st.dataframe(
                df_strany[["Kandidátní listina", "Celkem hlasů", "Podíl (%)", "Mandáty", "Srovnání s 2022 (Mandáty)"]].sort_values(by="Celkem hlasů", ascending=False), 
                use_container_width=True, 
                hide_index=True
            )

        # PRAVÁ ČÁST DASHBOARDU: ZVOLENÍ ZASTUPITELÉ S SROVNÁNÍM KROUŽKŮ
        with col_dash_right:
            st.subheader("👥 Zvolení zastupitelé (Srovnání preferenčních hlasů)")
            if data_live["zvoleni_kandidati"]:
                df_zvoleni = pd.DataFrame(data_live["zvoleni_kandidati"])

                def srovnej_krouzky(row):
                    jmeno = row["Jméno a příjmení"]
                    aktualni = row["Preferenční hlasy"]
                    if jmeno in past_votes_kand:
                        minule = past_votes_kand[jmeno]
                        rozdil = aktualni - minule
                        if rozdil > 0:
                            return f"🟢 +{rozdil} h. (minule {minule})"
                        elif rozdil < 0:
                            return f"🔴 {rozdil} h. (minule {minule})"
                        else:
                            return f"⚪ 0 h. (minule {minule})"
                    return "🆕 Nový zastupitel"

                df_zvoleni["Srovnání kroužků (oproti 2022)"] = df_zvoleni.apply(srovnej_krouzky, axis=1)

                st.dataframe(
                    df_zvoleni[["Poř.", "Jméno a příjmení", "Kandidátní listina", "Preferenční hlasy", "Srovnání kroužků (oproti 2022)"]].sort_values(by="Preferenční hlasy", ascending=False), 
                    use_container_width=True, 
                    hide_index=True
                )

# ==========================================
# KARTA 2: KOALIČNÍ KALKULÁTOR & RED-LINES
# ==========================================
with tab2:
    st.subheader("🤝 Koaliční kalkulátor a varianty většiny (≥ 11 křesel)")
    if data_live and data_live["strany"]:
        df_strany = pd.DataFrame(data_live["strany"])
        hlasy_dict = dict(zip(df_strany["Kandidátní listina"], df_strany["Celkem hlasů"]))
        mandaty_calc, _ = vypocitej_mandaty(hlasy_dict)

        vsechny_strany = list(hlasy_dict.keys())
        
        col_red1, col_red2 = st.columns(2)
        with col_red1:
            zakazane_strany = st.multiselect("🚫 Vyloučit z koalice (Red-line):", vsechny_strany, default=[])
        with col_red2:
            povinne_strany = st.multiselect("🔒 Nutná součást koalice:", vsechny_strany, default=[])

        koalice = najdi_koalice(mandaty_calc, min_kresel=11, zakazane=zakazane_strany, povinne=povinne_strany)

        if not koalice:
            st.warning("Při zvolených Red-Lines neexistuje žádná většina 11+ mandátů!")
        else:
            for combo, kresla, status_txt, status_class in koalice:
                party_badges = []
                for s in combo:
                    c = PARTY_COLORS.get(s, {"bg": "#6c757d", "text": "#ffffff"})
                    badge_html = f'<span style="background-color: {c["bg"]}; color: {c["text"]}; padding: 6px 12px; border-radius: 8px; margin-right: 6px; font-weight: bold; display: inline-block; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">{s}: {mandaty_calc[s]} m.</span>'
                    party_badges.append(badge_html)
                
                lead_color = PARTY_COLORS.get(combo[0], {"bg": "#084c61"})["bg"]
                
                st.markdown(f"""
                <div style="background-color: #ffffff; border-left: 6px solid {lead_color}; padding: 16px; border-radius: 12px; margin-bottom: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 1.15em; font-weight: 800; color: #0d2b35;">Celkem {kresla} mandátů</span>
                        <span class="{status_class}">{status_txt}</span>
                    </div>
                    <hr style="margin: 8px 0 12px 0; border-top: 1px solid #f0f4f7;">
                    <div>
                        {' '.join(party_badges)}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# KARTA 3: KOMPLETNÍ KANDIDÁTNÍ LISTINY
# ==========================================
with tab3:
    st.subheader("📜 Kompletní kandidátní listiny všech stran (Zvolení zastupitelé tučně)")
    if data_live and (data_live["vsechni_kandidati"] or data_live["zvoleni_kandidati"]):
        source_kandidati = data_live["vsechni_kandidati"] if data_live["vsechni_kandidati"] else data_live["zvoleni_kandidati"]
        df_all_cand = pd.DataFrame(source_kandidati)
        
        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            seznam_vsech_stran = ["Všechny kandidátky"] + list(df_all_cand["Kandidátní listina"].unique())
            vybrana_kandidatka = st.selectbox("Vyberte kandidátní listinu:", seznam_vsech_stran, key="k3_select")
        with col_f2:
            search_query = st.text_input("🔍 Vyhledat kandidáta podle jména:", "")

        df_show = df_all_cand.copy()
        if vybrana_kandidatka != "Všechny kandidátky":
            df_show = df_show[df_show["Kandidátní listina"] == vybrana_kandidatka]
            
        if search_query:
            df_show = df_show[df_show["Jméno a příjmení"].str.contains(search_query, case=False, na=False)]

        df_show["Status"] = df_show["Zvolen"].apply(lambda x: "✅ ZVOLEN/A" if x else "Náhradník")
        df_show["Jméno a příjmení (Zvolení tučně)"] = df_show.apply(
            lambda r: f"**{r['Jméno a příjmení']}**" if r["Zvolen"] else r["Jméno a příjmení"], 
            axis=1
        )

        st.dataframe(
            df_show[["Poř.", "Jméno a příjmení (Zvolení tučně)", "Kandidátní listina", "Preferenční hlasy", "Podíl hlasů (%)", "Status"]].sort_values(by=["Kandidátní listina", "Poř."]), 
            use_container_width=True, 
            hide_index=True
        )

# ==========================================
# KARTA 4: OKRSKY & VOLEBNÍ ÚČAST
# ==========================================
with tab4:
    st.subheader("🗺️ Detailní sčítání po domažlických okrscích")
    if data_live and data_live["ucast"]:
        u = data_live["ucast"]
        st.write(f"V Domažlicích je sečteno **{u['okrsky_zprac']} z {u['okrsky_celkem']} okrsků** ({u['okrsky_proc']:.1f} %).")
        st.progress(u['okrsky_proc'] / 100.0)