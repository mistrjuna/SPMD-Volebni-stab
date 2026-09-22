import streamlit as st
import pandas as pd
import numpy as np
import time
from itertools import combinations

st.set_page_config(page_title="Volební Štáb LIVE - Domažlice 2026", layout="wide", page_icon="🗳️")

# CSS Styl
st.markdown("""
<style>
    .metric-card { background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 15px; border-radius: 8px; text-align: center; }
</style>
""", unsafe_allow_html=True)

st.title("🗳️ Volební Štáb LIVE — Řídicí Centrum Domažlice")
st.caption("Komplexní aplikace pro volební noc: live data z okrsků, kroužkování, d'Hondtův přepočet, stabilita koalic a generátor pro media.")

# --- SIDEBAR: KONFIGURACE A RED-LINES ---
st.sidebar.header("⚙️ Nastavení & Red-Lines")
refresh_interval = st.sidebar.slider("Interval obnovy (sekund):", 10, 120, 30)

vsechny_strany = [
    "SDRUŽENÍ PRO MĚSTO DOMAŽLICE",
    "ANO 2011 a nezávislí",
    "Pro Domažlice (KDU-ČSL)",
    "ODS",
    "VAŠE DOMAŽLICE",
    "ŽIJEME DOMAŽLICE",
    "SPD",
    "Česká pirátská strana",
    "Stačilo!"
]

st.sidebar.subheader("🚫 Veto a Red-Lines")
zakazane_strany = st.sidebar.multiselect("Vyloučit z koalice (Red-line):", vsechny_strany, default=[])
povinne_strany = st.sidebar.multiselect("Nutná součást koalice:", vsechny_strany, default=[])

# --- ZÁLOŽKY ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Mandáty & Koalice", 
    "🗺️ Sledovač Okrsků (BOD 1)", 
    "✏️ Preferenční Hlasy & Skokani (BOD 2)", 
    "📣 Generátor pro Média & PR (BOD 4)"
])

# --- POMOCNÉ FUNKCE ---
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
                    # BOD 3: Hodnocení stability koalice
                    if kresla == 11:
                        status = "🔴 Okrajová / Riziková (11)"
                    elif kresla in [12, 13]:
                        status = "🟢 Bezpečná (12-13)"
                    else:
                        status = "🔵 Svrchovaná (14+)"
                    vysledky.append((combo, kresla, status))
                    
    vysledky.sort(key=lambda x: (x[1], len(x[0])))
    return vysledky

if "hlasy" not in st.session_state:
    st.session_state.hlasy = {
        "SDRUŽENÍ PRO MĚSTO DOMAŽLICE": 21200,
        "ANO 2011 a nezávislí": 20800,
        "Pro Domažlice (KDU-ČSL)": 14100,
        "ODS": 10500,
        "VAŠE DOMAŽLICE": 9200,
        "ŽIJEME DOMAŽLICE": 7800,
        "SPD": 7500,
        "Česká pirátská strana": 4200,
        "Stačilo!": 3900
    }

if "okrsky_secsteno" not in st.session_state:
    st.session_state.okrsky_secsteno = 8

mandaty, procenta = vypocitej_mandaty(st.session_state.hlasy)

# ==========================================
# TAB 1: MANDÁTY & KOALICE + METR STABILITY (BOD 3)
# ==========================================
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📈 Průběžný stav mandátů (21 křesel)")
        df_res = pd.DataFrame([
            {
                "Kandidátka": s, 
                "Hlasy": h, 
                "Podíl %": f"{procenta.get(s,0):.2f} %", 
                "Mandáty": mandaty.get(s,0),
                "Status": "✅ V Zastupitelstvu" if mandaty.get(s,0) > 0 else "❌ Pod 5 %"
            }
            for s, h in st.session_state.hlasy.items()
        ]).sort_values(by="Mandáty", ascending=False)
        
        st.dataframe(df_res, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("🤝 Koalice s Metrem Stability (≥ 11 křesel)")
        koalice = najdi_koalice(mandaty, min_kresel=11, zakazane=zakazane_strany, povinne=povinne_strany)
        
        if not koalice:
            st.warning("Žádná koalice nesplňuje nastavená pravidla a Red-Lines!")
        else:
            for combo, kresla, status in koalice:
                slozky = " + ".join([f"**{s}** ({mandaty[s]})" for s in combo])
                st.success(f"**{kresla} křesel** [{status}]: {slozky}")

# ==========================================
# TAB 2: SLEDOVAČ OKRSKŮ (BOD 1)
# ==========================================
with tab2:
    st.subheader("🗺️ Průběh sčítání v domažlických okrscích")
    
    secsteno_pct = (st.session_state.okrsky_secsteno / 14) * 100
    st.progress(secsteno_pct / 100)
    st.write(f"**Sečteno: {st.session_state.okrsky_secsteno} z 14 okrsků ({secsteno_pct:.1f} %)**")
    
    okrsky_data = [
        {"Okrsek": "Č. 1 - ZŠ Komenského", "Oblast": "Centrum / Město", "Stav": "✅ Sečteno", "Historický sklon": "SPMD / Pro Domažlice"},
        {"Okrsek": "Č. 2 - Gymnázium J. Š. Baara", "Oblast": "Hořejší Předměstí", "Stav": "✅ Sečteno", "Historický sklon": "ODS / SPMD"},
        {"Okrsek": "Č. 3 - SOŠ Domažlice", "Oblast": "Bezděkovské Předměstí", "Stav": "✅ Sečteno", "Historický sklon": "Pro Domažlice / Vaše Domažlice"},
        {"Okrsek": "Č. 4 - MŠ Poděbradova", "Oblast": "Dolejší Předměstí", "Stav": "✅ Sečteno", "Historický sklon": "Vaše Domažlice / Piráti"},
        {"Okrsek": "Č. 5 - Sídliště Křížová", "Oblast": "Sídliště", "Stav": "⏳ Sčítá se...", "Historický sklon": "ANO / SPD"},
        {"Okrsek": "Č. 6 - Sídliště Palackého", "Oblast": "Sídliště", "Stav": "⏳ Sčítá se...", "Historický sklon": "ANO / Stačilo!"},
        {"Okrsek": "Č. 7 - Týnské Předměstí", "Oblast": "Rodinné domy", "Stav": "✅ Sečteno", "Historický sklon": "SPMD / ODS"},
        {"Okrsek": "Č. 8 - Havlovice", "Oblast": "Místní část", "Stav": "✅ Sečteno", "Historický sklon": "Pro Domažlice"},
        {"Okrsek": "Č. 9 - Smržovice / Ždánov", "Oblast": "Místní část", "Stav": "✅ Sečteno", "Historický sklon": "Pravice / Nezávislí"},
        {"Okrsek": "Č. 10 - Školní ulice", "Oblast": "Školní čtvrť", "Stav": "✅ Sečteno", "Historický sklon": "Žijeme Domažlice"},
    ]
    st.dataframe(pd.DataFrame(okrsky_data), use_container_width=True, hide_index=True)

# ==========================================
# TAB 3: PREFERENČNÍ HLASY & SKOKANI (BOD 2)
# ==========================================
with tab3:
    st.subheader("✏️ Preferenční hlasy & Detektor Skokanů")
    st.info("Sledování candidateských posunů (překročení 5 % preferenčních hlasů v rámci listiny).")
    
    skokani_demo = [
        {"Kandidátka": "SDRUŽENÍ PRO MĚSTO DOMAŽLICE", "Kandidát": "MUDr. Kamil Zábranský", "Původní #": 3, "Nové #": 1, "Kroužky %": "14.2 %", "Status": "🔥 Skokan (Posun na 1. místo)"},
        {"Kandidátka": "Pro Domažlice (KDU-ČSL)", "Kandidát": "Bc. Stanislav Antoš", "Původní #": 1, "Nové #": 1, "Kroužky %": "18.5 %", "Status": "✅ Potvrdil lídra"},
        {"Kandidátka": "VAŠE DOMAŽLICE", "Kandidát": "Ing. Viktor Krutina", "Původní #": 1, "Nové #": 1, "Kroužky %": "11.1 %", "Status": "✅ Potvrdil lídra"},
        {"Kandidátka": "ŽIJEME DOMAŽLICE", "Kandidátka": "Mgr. Hana Hradecká", "Původní #": 1, "Nové #": 1, "Kroužky %": "9.8 %", "Status": "✅ Potvrdil lídra"},
    ]
    st.dataframe(pd.DataFrame(skokani_demo), use_container_width=True, hide_index=True)

# ==========================================
# TAB 4: PR & GENERÁTOR PRO MÉDIA (BOD 4)
# ==========================================
with tab4:
    st.subheader("📣 PR Generátor pro Média & Sociální Sítě")
    
    st.write("### 📝 Rychlé tiskové vyjádření")
    text_pr = f"""
VOLEBNÍ PROHLÁŠENÍ — DOMAŽLICE 2026

Děkujeme všem voličům v Domažlicích za účast v komunálních volbách a podporu.

Podle průběžných výsledků (sečteno {st.session_state.okrsky_secsteno}/14 okrsků) získávají subjekty tyto mandáty:
- SPMD: {mandaty.get('SDRUŽENÍ PRO MĚSTO DOMAŽLICE',0)} mandátů
- ANO: {mandaty.get('ANO 2011 a nezávislí',0)} mandátů
- Pro Domažlice: {mandaty.get('Pro Domažlice (KDU-ČSL)',0)} mandátů
- ODS: {mandaty.get('ODS',0)} mandátů
- VAŠE DOMAŽLICE: {mandaty.get('VAŠE DOMAŽLICE',0)} mandátů
- ŽIJEME DOMAŽLICE: {mandaty.get('ŽIJEME DOMAŽLICE',0)} mandátů

Jsme připraveni zahájit jednání o stabilním vedení města Domažlice na další 4 roky.
"""
    st.text_area("Předpřipravený text pro tisk a FB:", text_pr, height=220)