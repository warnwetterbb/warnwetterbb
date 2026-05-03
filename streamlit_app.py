import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# Seiteneinstellungen
st.set_page_config(page_title="DWD Wettermodell (Brightsky)", layout="wide")

st.title("DWD Wettermodell Monitor")
st.info("Direktzugriff auf ICON-D2 & ICON-EU via Brightsky API (DWD OpenData)")

# --- Sidebar ---
st.sidebar.header("Konfiguration")
model_choice = st.sidebar.selectbox("Wettermodell", ["icon-d2", "icon-eu"])
lat = st.sidebar.number_input("Breitengrad (Lat)", value=52.52, step=0.01) # Default Berlin
lon = st.sidebar.number_input("Längengrad (Lon)", value=13.40, step=0.01)

# --- API Abfrage ---
@st.cache_data(ttl=3600)
def get_weather_data(model, lat, lon):
    # Brightsky API Endpunkt
    url = f"https://api.brightsky.dev/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "date": datetime.now().isoformat(),
        "last_date": datetime.now().replace(day=datetime.now().day + 2).isoformat(), # 48h Vorschau
        "dwd_model": model
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# --- Datenverarbeitung ---
data_json = get_weather_data(model_choice, lat, lon)

if data_json and "weather" in data_json:
    df = pd.DataFrame(data_json["weather"])
    # Zeitstempel konvertieren
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Auswahl der Parameter
    st.subheader(f"Vorhersage für {lat}, {lon} ({model_choice.upper()})")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Temperatur (2m)", f"{df['temperature'].iloc[0]} °C")
        fig_temp = px.line(df, x="timestamp", y="temperature", title="Temperatur (°C)", template="plotly_dark")
        st.plotly_chart(fig_temp, use_container_width=True)

    with col2:
        st.metric("Niederschlag", f"{df['precipitation'].iloc[0]} mm/h")
        fig_prec = px.bar(df, x="timestamp", y="precipitation", title="Niederschlag (mm/h)", template="plotly_dark")
        st.plotly_chart(fig_prec, use_container_width=True)

    with col3:
        # Windböen (wind_gust)
        st.metric("Windböen", f"{df['wind_gust'].iloc[0]} km/h")
        fig_wind = px.line(df, x="timestamp", y="wind_gust", title="Windböen (km/h)", template="plotly_dark")
        st.plotly_chart(fig_wind, use_container_width=True)

    with st.expander("Tabellarische Daten"):
        st.dataframe(df)
else:
    st.error("Fehler beim Abrufen der Daten von der Brightsky API.")
