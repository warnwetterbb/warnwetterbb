import streamlit as st
import pandas as pd
import plotly.express as px
# Wir nutzen NUR den absolut stabilen Basis-Pfad
from wetterdienst.provider.dwd.model import DwdModelRequest

# Seiteneinstellungen
st.set_page_config(page_title="DWD Wetter-Monitor", layout="wide")

st.title("ICON Wettermodell Viewer")
st.markdown("---")

# --- Sidebar ---
st.sidebar.header("Optionen")
model_choice = st.sidebar.selectbox("Modell", ["icon-d2", "icon-eu"])
param_choice = st.sidebar.selectbox(
    "Parameter", 
    ["temperature_air_mean_200", "precipitation_height_significant_weather_last_1h", "wind_gust_max_last_1h_10m"],
    format_func=lambda x: "Temperatur" if "temp" in x else ("Niederschlag" if "precip" in x else "Windböen")
)

@st.cache_data(ttl=3600)
def fetch_data(m_id, p_id):
    try:
        # Direkte Abfrage ohne Umwege über Sub-Packages
        request = DwdModelRequest(
            parameter=[p_id],
            model=m_id
        )
        # Suche nach Station Berlin-Brandenburg (ID: 10382)
        station_data = request.filter_by_station_id(station_id="10382")
        return station_data.values.all().to_pandas()
    except Exception as e:
        return str(e)

# --- Hauptbereich ---
with st.spinner('Empfange Daten vom DWD...'):
    result = fetch_data(model_choice, param_choice)

if isinstance(result, str):
    st.error(f"Kritischer Fehler beim Laden: {result}")
    st.info("Versuche die Seite in wenigen Minuten neu zu laden. Manchmal ist die API kurzzeitig überlastet.")
elif result is not None and not result.empty:
    st.subheader(f"Vorhersage für Berlin (Modell: {model_choice.upper()})")
    
    # Chart Erstellung
    fig = px.line(
        result, 
        x="date", 
        y="value", 
        labels={"value": "Messwert", "date": "Zeitpunkt (UTC)"},
        template="plotly_dark"
    )
    fig.update_traces(line_color='#00d1b2', mode="lines+markers")
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabelle
    with st.expander("Tabellarische Daten"):
        st.dataframe(result)
else:
    st.warning("Keine Daten für diese Kombination verfügbar.")
