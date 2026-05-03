import streamlit as st
from wetterdienst.provider.dwd.forecast import DwdForecastRequest, DwdForecastModel
import pandas as pd
import plotly.express as px

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

# Mapping der Parameter auf DWD-Interne Namen
param_map = {
    "2m Temperatur": "temperature_air_mean_200",
    "Niederschlag pro Stunde": "precipitation_height_significant_weather_last_1h",
    "Windböen": "wind_gust_max_last_1h_10m"
}

# --- Daten abrufen ---
@st.cache_data(ttl=3600)  # Cache für 1 Stunde, um Server zu schonen
def get_weather_data(model_name, param_name):
    model = DwdForecastModel.ICON_D2 if model_name == "ICON-D2" else DwdForecastModel.ICON_EU
    
    # Beispiel-Koordinaten (Berlin). 
    # Hinweis: Für ganze Karten müssten GRIB-Files geladen werden, 
    # was im Streamlit-Cloud-RAM oft zu schwer ist. Hier nutzen wir Punkt-Vorhersagen.
    request = DwdForecastRequest(
        parameter=[param_name],
        model=model
    )
    
    # Wir suchen nach der Station Berlin-Brandenburg (oder lasse den User wählen)
    stations = request.filter_by_station_id(station_id="10382") # Berlin
    return stations.values.all().to_pandas()

try:
    with st.spinner('Lade Daten vom DWD...'):
        df = get_weather_data(model_choice, param_map[parameter_choice])

    # --- Darstellung ---
    st.subheader(f"{parameter_choice} - {model_choice} (Station: Berlin)")
    
    if not df.empty:
        # Plotly Chart erstellen
        fig = px.line(
            df, 
            x="date", 
            y="value", 
            labels={"value": parameter_choice, "date": "Zeit (UTC)"},
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Datentabelle
        with st.expander("Rohdaten anzeigen"):
            st.dataframe(df)
    else:
        st.warning("Keine Daten für diese Auswahl gefunden.")

except Exception as e:
    st.error(f"Fehler beim Laden der Daten: {e}")

