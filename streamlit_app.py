import streamlit as st
import pandas as pd
import plotly.express as px
# Wir nutzen nur die stabilen Model-Klassen
from wetterdienst.provider.dwd.model import DwdModelRequest

# Seiteneinstellungen
st.set_page_config(page_title="DWD Wettermodell Viewer", layout="wide")

st.title("Weather Model Dashboard (DWD)")
st.info("Visualisierung der ICON-D2 & ICON-EU Modelldaten")

# --- Sidebar zur Auswahl ---
st.sidebar.header("Konfiguration")
model_choice = st.sidebar.selectbox("Wettermodell", ["ICON-D2", "ICON-EU"])
parameter_choice = st.sidebar.selectbox(
    "Parameter", 
    ["2m Temperatur", "Niederschlagsrate", "Windböen"]
)

# Mapping der Parameter auf DWD-Standards
# Diese Namen sind in der wetterdienst-API für ICON-Modelle stabil
param_map = {
    "2m Temperatur": "temperature_air_mean_200",
    "Niederschlagsrate": "precipitation_height_significant_weather_last_1h",
    "Windböen": "wind_gust_max_last_1h_10m"
}

@st.cache_data(ttl=3600)
def load_dwd_data(model_label, param_id):
    # Mapping auf die internen Model-IDs der Library
    m_id = "icon-d2" if model_label == "ICON-D2" else "icon-eu"
    
    try:
        # Request-Objekt für Point-Forecasts (Stationen)
        request = DwdModelRequest(
            parameter=[param_id],
            model=m_id
        )
        
        # Wir nutzen eine feste Station für den ersten Test (Berlin-Brandenburg: 10382)
        # Man kann später eine Suche für Koordinaten hinzufügen
        result = request.filter_by_station_id(station_id="10382")
        df = result.values.all().to_pandas()
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})

# --- Main Logic ---
with st.spinner('Lade Daten vom DWD OpenData Server...'):
    data = load_dwd_data(model_choice, param_map[parameter_choice])

if "error" in data.columns:
    st.error(f"Datenbezug fehlgeschlagen: {data['error'].iloc[0]}")
    st.warning("Hinweis: Manchmal sind hochauflösende D2-Daten für bestimmte Zeitfenster kurzzeitig nicht verfügbar.")
elif not data.empty:
    # Daten-Visualisierung
    st.subheader(f"{parameter_choice} ({model_choice}) - Station Berlin")
    
    fig = px.line(
        data, 
        x="date", 
        y="value", 
        labels={"value": parameter_choice, "date": "Zeit (UTC)"},
        template="plotly_dark",
        line_shape="linear"
    )
    
    # Tooltip und Design-Anpassung
    fig.update_traces(mode="lines+markers")
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("Tabellarische Ansicht"):
        st.write(data)
else:
    st.warning("Keine Daten gefunden. Bitte versuche ein anderes Modell oder einen anderen Parameter.")

