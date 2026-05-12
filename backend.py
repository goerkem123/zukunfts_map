import pandas as pd
import streamlit as st
from geopy.geocoders import ArcGIS
import time

@st.cache_data
def lade_daten_und_koordinaten():
    # 1. Excel einlesen
    df = pd.read_excel("firmen.xlsx")
    
    # 2. Alle Spaltennamen säubern
    df.columns = df.columns.str.strip()
    
    # 3. Textdaten säubern
    for col in ["Firma", "Stadt", "Bereich"]:
        df[col] = df[col].astype(str).str.strip()
    
    # 4. Sicherstellen, dass Bewertung und Logo da sind (auch wenn leer)
    if "Logo_URL" not in df.columns: df["Logo_URL"] = ""
    if "Bewertung" not in df.columns: df["Bewertung"] = 0
    
    # 5. Geocoding mit ArcGIS (schnell & zuverlässig)
    geolocator = ArcGIS()
    breitengrade = []
    laengengrade = []
    
    print("\n🚀 Suche Koordinaten für neue Liste...")
    for stadt in df["Stadt"]:
        try:
            location = geolocator.geocode(f"{stadt}, Deutschland", timeout=10)
            if location:
                breitengrade.append(location.latitude)
                laengengrade.append(location.longitude)
            else:
                breitengrade.append(None)
                laengengrade.append(None)
        except:
            breitengrade.append(None)
            laengengrade.append(None)
        time.sleep(0.1) 
            
    df["Breitengrad"] = breitengrade
    df["Laengengrad"] = laengengrade
    
    return df.dropna(subset=["Breitengrad", "Laengengrad"])

def update_bewertung(firma_name, neue_note):
    # Excel laden
    df = pd.read_excel("firmen.xlsx")
    df.columns = df.columns.str.strip()
    
    # Die Zeile finden und Note ändern (wir nutzen .loc)
    df.loc[df['Firma'] == firma_name, 'Bewertung'] = neue_note
    
    # Speichern
    df.to_excel("firmen.xlsx", index=False)
    
    # Cache löschen, damit die App die Änderung sofort sieht
    st.cache_data.clear()