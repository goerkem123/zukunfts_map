import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from backend import lade_daten_und_koordinaten 
from folium.plugins import MarkerCluster

# 1. KONFIGURATION
st.set_page_config(page_title="GG Karriere Hub Pro", page_icon="💼", layout="wide")

# --- DER ULTIMATIVE UI-FIX (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #f8fafc;
        background-color: #0f172a !important;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #020617 !important; 
        border-right: 1px solid #1e293b;
    }

    /* FIX: Sidebar Labels */
    [data-testid="stWidgetLabel"] p {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }

    /* --- MULTISELECT: REINSCHREIBEN VERBIETEN & BLOB KILLEN --- */
    /* 1. Tippen komplett blockieren */
    div[data-baseweb="select"] input {
        pointer-events: none !important;
        caret-color: transparent !important;
        user-select: none !important;
    }

    /* 2. Den "Blob" links (Such-Icon Container) radikal entfernen */
    div[data-baseweb="select"] div[role="presentation"] {
        display: none !important;
    }
    
    /* Falls Streamlit das Icon anders benennt - alle Icons im Select verstecken */
    div[data-baseweb="select"] svg[viewBox="0 0 24 24"] {
        display: none !important;
    }

    /* Den dunklen Hintergrund-Schatten im Feld löschen */
    div[data-baseweb="select"] > div:first-child {
        background-color: transparent !important;
    }

    /* 3. Die Tags (Bio/IT) sauber stylen */
    span[data-baseweb="tag"] {
        background-color: #3b82f6 !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
    }
    span[data-baseweb="tag"] * {
        background-color: transparent !important;
    }

    /* INPUT FELDER ALLGEMEIN */
    div[data-baseweb="select"], div[data-baseweb="input"] {
        background-color: #1e293b !important;
        border-radius: 10px !important;
        border: 1px solid #334155 !important;
    }

    /* METRIC CARDS */
    div[data-testid="stMetric"] {
        background: #020617 !important;
        border: 1px solid #1e293b !important;
        padding: 1.5rem !important;
        border-radius: 16px !important;
    }
    div[data-testid="stMetricLabel"] > div > p { color: #3b82f6 !important; }
    div[data-testid="stMetricValue"] > div { color: #f8fafc !important; font-weight: 700 !important; }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600 !important;
        color: #94a3b8 !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: #3b82f6 !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Daten laden
df = lade_daten_und_koordinaten()

# --- HELPER ---
def get_stars(val):
    try:
        n = int(float(val))
        return "★" * n + "☆" * (5-n) if 0 < n <= 5 else "—"
    except: return "—"

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="color:white; font-size:1.6rem; font-weight:700; margin-bottom:2rem;">CareerHub <span style="color:#3b82f6">GG</span></div>', unsafe_allow_html=True)
    
    st.markdown("### 🔍 Filter & Suche")
    suche = st.text_input("Name der Firma", placeholder="Suchen...")
    auswahl = st.multiselect("Bereich", options=["Bio", "IT"], default=["Bio", "IT"])
    
    st.markdown("---")
    
    st.markdown("### ✨ Quick Rate")
    f_name = st.selectbox("Unternehmen", sorted(df['Firma'].unique()))
    rating = st.feedback("stars")
    if rating is not None:
        if st.button("Rating speichern", use_container_width=True):
            from backend import update_bewertung
            update_bewertung(f_name, rating + 1)
            st.success("Gespeichert!")
            st.rerun()

# --- LOGIK ---
mask = df["Bereich"].isin(auswahl)
if suche:
    mask = mask & df["Firma"].str.contains(suche, case=False)
df_view = df[mask]

# --- MAIN UI ---
st.markdown('<h1 style="color:white; font-size:3rem; font-weight:800;">Dashboard</h1>', unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Gesamt", len(df_view))
m2.metric("Gözde (Bio)", len(df_view[df_view['Bereich'] == 'Bio']))
m3.metric("Görkem (IT)", len(df_view[df_view['Bereich'] == 'IT']))

st.write("")

tab1, tab2, tab3 = st.tabs(["🗺️ Karte", "📊 Analyse", "📋 Listen"])

# --- TAB 1: KARTE ---
with tab1:
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles="CartoDB positron")
    cluster = MarkerCluster().add_to(m)

    for _, row in df_view.iterrows():
        stars = get_stars(row['Bewertung'])
        icon_emoji = "🧬" if row["Bereich"] == "Bio" else "💻"
        color = "#dbeafe" if row["Bereich"] == "Bio" else "#fee2e2"
        border = "#2563eb" if row["Bereich"] == "Bio" else "#dc2626"
        
        icon_html = f"""
            <div style="background-color:{color}; border:1.5px solid {border}; border-radius:10px; width:32px; height:32px; 
            display:flex; align-items:center; justify-content:center; font-size:16px; box-shadow:0 4px 8px rgba(0,0,0,0.3);">
                {icon_emoji}
            </div>
        """
        folium.Marker(
            [row["Breitengrad"], row["Laengengrad"]],
            icon=folium.DivIcon(html=icon_html),
            popup=folium.Popup(f'<div style="text-align:center; color:#1e293b;"><b>{row["Firma"]}</b><br>{stars}</div>', max_width=150)
        ).add_to(cluster)
    
    st_folium(m, width="100%", height=600, use_container_width=True)

# --- TAB 2: ANALYSE ---
with tab2:
    st.subheader("Top Standorte")
    if not df_view.empty:
        counts = df_view['Stadt'].value_counts().head(10)
        col_chart, col_data = st.columns([2, 1])
        with col_chart:
            st.bar_chart(counts, color="#3b82f6")
        with col_data:
            st.dataframe(counts, use_container_width=True)
    else:
        st.info("Keine Daten vorhanden.")

# --- TAB 3: LISTEN ---
with tab3:
    st.subheader("Detail-Listen")
    df_stars = df_view.copy()
    df_stars["Sterne"] = df_stars["Bewertung"].apply(get_stars)
    st.dataframe(df_stars[["Firma", "Stadt", "Sterne", "Bereich"]], hide_index=True, use_container_width=True)