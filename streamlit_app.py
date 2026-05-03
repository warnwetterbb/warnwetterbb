import streamlit as st
import pandas as pd
import plotly.express as px
# Korrigierter Import für wetterdienst >= 0.120.0
from wetterdienst.provider.dwd.mosmix import DwdMosmixRequest, DwdMosmixType
from wetterdienst.provider.dwd.model import DwdModelRequest

# Seiteneinstellungen
st.set_page_config(page_title="DWD Wettermodell Viewer", layout="wide")

st.title("Weather Model Dashboard (DWD OpenData)")
st.info("Datenquelle: ICON-D2 & ICON-EU via Wetterdienst Library")

# --- Sidebar zur Auswahl ---
st.sidebar.header("Einstellungen")
model_choice = st.sidebar.selectbox("Wettermodell wählen", ["ICON-D2", "ICON-EU"])
parameter_choice = st.sidebar.selectbox(
    "Parameter wählen", 
    ["2m Temperatur", "Niederschlag pro Stunde", "Windböen"]
)

# Mapping der Parameter auf DWD-Interne Namen (ICON Standard)
param_map = {
    "2m Temperatur": "temperature_air_mean_200",
    "Niederschlag pro Stunde": "precipitation_height_significant_weather_last_1h",
    "Windböen": "wind_gust_max_last_1h_10m"
}

# --- Daten abrufen ---
@st.cache_data(ttl=3600)
def get_weather_data(model_name, param_name):
    # Auswahl des Modells über den neuen DwdModelRequest
    # Wir nutzen hier die Point-Request Methode für eine Station (z.B. Berlin-Tegel: 10382)
    model_id = "icon-d2" if model_name == "ICON-D2" else "icon-eu"
    
    try:
        request = DwdModelRequest(
            parameter=[param_name],
            model=model_id
        )
        
        # Filter auf eine Station (Berlin)
        stations = request.filter_by_station_id(station_id="10382")
        values = stations.values.all()
        return values.to_pandas()
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

# --- Hauptteil der App ---
try:
    with st.spinner('Lade Modelldaten...'):
        df = get_weather_data(model_choice, param_map[parameter_choice])

    if "error" in df.columns:
        st.error(f"Fehler beim Abrufen der Daten: {df['error'].iloc[0]}")
    elif not df.empty:
        st.subheader(f"{parameter_choice} - {model_choice} (Station: Berlin)")
        
        # Plotly Chart
        fig = px.line(
            df, 
            x="date", 
            y="value", 
            labels={"value": parameter_choice, "date": "Zeit (UTC)"},
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("Rohdaten anzeigen"):
            st.dataframe(df)
    else:
        st.warning("Keine Daten verfügbar. Möglicherweise ist der DWD-Server gerade ausgelastet.")

except Exception as e:
    st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
