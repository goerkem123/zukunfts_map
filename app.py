import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from backend import lade_daten_und_koordinaten 
from folium.plugins import MarkerCluster  # <--- HIER war der Fehler!

# 1. Webseite & Branding
st.set_page_config(page_title="Karriere-Hub Pro", page_icon="💼", layout="wide")
df = lade_daten_und_koordinaten()

# --- HILFSFUNKTION FÜR STERNE (Robust & Sicher) ---
def konvertiere_zu_sternen(wert):
    try:
        # Versuche den Wert in eine Ganzzahl umzuwandeln (egal ob 5, 5.0 oder "5")
        anzahl = int(float(wert))
        if anzahl > 0:
            return "⭐" * anzahl
    except:
        pass
    return "-"

# 2. SIDEBAR
with st.sidebar:
    st.title("🔍 Filter & Suche")
    suche = st.text_input("Firma suchen...", placeholder="z.B. Microsoft")
    rollen_mapping = {"Bio": "Gözde (Bio)", "IT": "Görkem (IT)"}
    auswahl = st.multiselect("Wer sucht?", options=["Bio", "IT"], default=["Bio", "IT"], format_func=lambda x: rollen_mapping[x])
    
    # LIVE BEWERTUNG
    st.markdown("---")
    st.subheader("⭐ Firma live bewerten")
    firma_auswahl = st.selectbox("Firma wählen:", sorted(df['Firma'].unique()))
    score = st.feedback("stars")
    if score is not None:
        neue_note = score + 1
        if st.button(f"{neue_note} Sterne für {firma_auswahl} speichern"):
            from backend import update_bewertung
            update_bewertung(firma_auswahl, neue_note)
            st.success("Gespeichert! Bitte Seite neu laden.")
            st.rerun()

# 3. FILTER-LOGIK
maske = df["Bereich"].isin(auswahl)
if suche:
    maske = maske & df["Firma"].str.contains(suche, case=False)
df_gefiltert = df[maske]

# 4. HAUPTSEITE MIT DREI TABS
st.title("💼 Unser Karriere-Hub: Gözde & Görkem")

# Hier fügen wir den dritten Tab hinzu
tab1, tab2, tab3 = st.tabs(["🗺️ Interaktive Karte", "📊 Standort-Analyse", "⭐ Bewertungen"])

# --- TAB 1: KARTE ---
with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Firmen im Fokus", len(df_gefiltert))
    col2.metric("Gözde (Bio)", len(df_gefiltert[df_gefiltert['Bereich'] == 'Bio']))
    col3.metric("Görkem (IT)", len(df_gefiltert[df_gefiltert['Bereich'] == 'IT']))

    # Karte erstellen
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles="CartoDB positron")
    
    # NEU: Das Cluster-Objekt erstellen
    marker_cluster = MarkerCluster().add_to(m)

    for index, reihe in df_gefiltert.iterrows():
        # Sterne & Logo Logik
        sterne_text = konvertiere_zu_sternen(reihe['Bewertung'])
        logo = reihe['Logo_URL'] if pd.notna(reihe['Logo_URL']) and str(reihe['Logo_URL']).startswith("http") else "https://via.placeholder.com/50"
        
        popup_html = f"""
        <div style="text-align: center; min-width: 150px;">
            <img src="{logo}" width="50" style="border-radius: 5px;"><br>
            <b>{reihe['Firma']}</b><br>
            {sterne_text}
        </div>
        """
        
        farbe = "blue" if reihe["Bereich"] == "Bio" else "red"
        
        # Den Marker jetzt zum 'marker_cluster' hinzufügen, nicht direkt zu 'm'
        folium.Marker(
            location=[reihe["Breitengrad"], reihe["Laengengrad"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=reihe["Firma"],
            icon=folium.Icon(color=farbe, icon="briefcase", prefix='fa')
        ).add_to(marker_cluster)

    # Die Karte im Streamlit-Tab anzeigen
    st_folium(m, width="100%", height=550)

# --- TAB 2: NUR DIAGRAMME ---
with tab2:
    st.subheader("🏙️ Standort-Ranking")
    city_counts = df_gefiltert['Stadt'].value_counts()
    col_chart, col_data = st.columns([2, 1])
    with col_chart:
        st.bar_chart(city_counts)
    with col_data:
        st.dataframe(city_counts, column_config={"count": "Anzahl"}, use_container_width=True)

# --- TAB 3: NUR BEWERTUNGEN (Die getrennten Listen) ---
with tab3:
    st.subheader("⭐ Unsere Favoriten im Detail")
    
    df_show = df_gefiltert.copy()
    df_show["Sterne"] = df_show["Bewertung"].apply(konvertiere_zu_sternen)

    col_goezde, col_goerkem = st.columns(2)

    with col_goezde:
        st.markdown("### 🧬 Gözde (Bio)")
        df_bio = df_show[df_show['Bereich'] == 'Bio'].sort_values(by="Firma")
        st.dataframe(df_bio[["Firma", "Stadt", "Sterne"]], use_container_width=True, hide_index=True)

    with col_goerkem:
        st.markdown("### 💻 Görkem (IT)")
        df_it = df_show[df_show['Bereich'] == 'IT'].sort_values(by="Firma")
        st.dataframe(df_it[["Firma", "Stadt", "Sterne"]], use_container_width=True, hide_index=True)