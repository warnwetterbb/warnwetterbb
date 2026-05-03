import streamlit as st
import requests
from io import BytesIO
from PIL import Image

# Seiteneinstellungen (Aktualisiert auf neue Streamlit-Standards)
st.set_page_config(page_title="DWD Weather Maps", layout="wide")

st.title("🗺️ DWD Modellkarten (Echtzeit)")

# --- Sidebar mit Radio-Buttons (Keine Tastatur nötig) ---
st.sidebar.header("Karten-Optionen")

region_choice = st.sidebar.radio(
    "Region wählen:",
    ["Mitteleuropa", "Deutschland", "Berlin/Brandenburg"]
)

model_choice = st.sidebar.radio(
    "Modell wählen:",
    ["ICON-D2 (Feinmaschig)", "ICON-EU (Europa)"]
)

param_choice = st.sidebar.radio(
    "Parameter wählen:",
    ["2m Temperatur", "Niederschlagsrate", "Windböen"]
)

# --- Konfiguration ---

# Bounding Boxes (West, Süd, Ost, Nord)
bbox_map = {
    "Mitteleuropa": "2.0,43.0,22.0,58.0",
    "Deutschland": "5.5,47.0,15.5,55.5",
    "Berlin/Brandenburg": "11.0,51.0,15.0,54.0"
}

# Mapping für Layer-Namen (Präzise DWD Geoserver Namen)
model_key = "icon-d2_germany" if "D2" in model_choice else "icon-eu_europe"
param_key = {
    "2m Temperatur": "2m_temperature",
    "Niederschlagsrate": "total_precipitation",
    "Windböen": "maximum_wind_gust_10m"
}

layer_name = f"dwd:{model_key}_single_level_elements_{param_key[param_choice]}"

@st.cache_data(ttl=600) # 10 Minuten Cache
def get_static_map(layer, bbox):
    wms_url = "https://maps.dwd.de/geoserver/dwd/wms"
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": layer,
        "STYLES": "",
        "BBOX": bbox,
        "WIDTH": "1200",
        "HEIGHT": "800",
        "CRS": "EPSG:4326",
        "FORMAT": "image/png",
        "TRANSPARENT": "FALSE"
    }
    
    try:
        response = requests.get(wms_url, params=params, timeout=15)
        # Prüfen, ob es wirklich ein Bild ist und kein XML-Fehler
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            return response.content
        else:
            return f"Fehler: Server meldet {response.status_code} oder kein Bild empfangen."
    except Exception as e:
        return f"Verbindungsfehler: {str(e)}"

# --- Anzeige-Logik ---
st.subheader(f"{param_choice} ({model_choice}) - {region_choice}")

with st.spinner("Lade Karte direkt vom DWD Geoserver..."):
    result = get_static_map(layer_name, bbox_map[region_choice])
    
    if isinstance(result, bytes):
        # Bild anzeigen mit neuem Parameter width='stretch'
        st.image(result, width='stretch')
        
        # Legende in der Sidebar
        st.sidebar.markdown("---")
        st.sidebar.write("**Legende:**")
        legend_url = f"https://maps.dwd.de/geoserver/dwd/wms?service=WMS&request=GetLegendGraphic&format=image/png&layer={layer_name}"
        st.sidebar.image(legend_url)
    else:
        # Fehlermeldung anzeigen, falls kein Bild kommt
        st.error(result)
        st.warning("HINWEIS: Manche D2-Layer sind nur für Deutschland verfügbar. Wähle 'Deutschland' als Region.")

st.sidebar.info("Datenquelle: DWD OpenData Geoserver")
