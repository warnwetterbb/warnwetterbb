import streamlit as st
import requests
from io import BytesIO

# Seiteneinstellungen
st.set_page_config(page_title="DWD Modellkarten Statisch", layout="wide")

st.title("🗺️ DWD Modellkarten - Statische 2D Ansicht")

# --- Auswahl-Menüs in der Sidebar (Nur Radio Buttons) ---
st.sidebar.header("Karten-Konfiguration")

region = st.sidebar.radio(
    "1. Region wählen",
    ["Deutschland", "Berlin/Brandenburg", "Mitteleuropa"]
)

model = st.sidebar.radio(
    "2. Wettermodell",
    ["ICON-D2 (Regional)", "ICON-EU (Europa)"]
)

parameter = st.sidebar.radio(
    "3. Wetter-Parameter",
    ["2m Temperatur", "Niederschlagsrate", "Windböen"]
)

# --- Logik für die Karten-Anforderung (WMS) ---

# Definition der Bounding-Boxen (West, Süd, Ost, Nord)
bbox_map = {
    "Deutschland": "5.8,47.2,15.1,55.1",
    "Berlin/Brandenburg": "11.5,51.2,15.0,53.8",
    "Mitteleuropa": "2.0,43.0,22.0,58.0"
}

# Mapping der Layer-Namen des DWD Geoservers
layer_base = "icon-d2_germany" if "D2" in model else "icon-eu_europe"
param_map = {
    "2m Temperatur": "2m_temperature",
    "Niederschlagsrate": "total_precipitation",
    "Windböen": "maximum_wind_gust_10m"
}

layer_name = f"dwd:{layer_base}_single_level_elements_{param_map[parameter]}"

def get_dwd_map(layers, bbox):
    """Holt die statische Karte als PNG vom DWD Geoserver"""
    wms_url = "https://maps.dwd.de/geoserver/dwd/wms"
    params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": layers,
        "styles": "",
        "bbox": bbox,
        "width": "1200",
        "height": "800",
        "srs": "EPSG:4326", # Geografische Projektion
        "format": "image/png",
        "transparent": "false"
    }
    
    try:
        response = requests.get(wms_url, params=params, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        return e

# --- Anzeige ---
st.subheader(f"Aktuelle Karte: {parameter} | {model} | {region}")

with st.spinner("Generiere Karte vom DWD OpenData Server..."):
    map_image = get_dwd_map(layer_name, bbox_map[region])
    
    if isinstance(map_image, bytes):
        # Karte anzeigen
        st.image(map_image, use_container_width=True)
        
        # Legende passend dazu laden
        st.sidebar.markdown("---")
        st.sidebar.write("**Legende:**")
        legend_url = f"https://maps.dwd.de/geoserver/dwd/wms?request=GetLegendGraphic&format=image/png&layer={layer_name}"
        st.sidebar.image(legend_url)
    else:
        st.error(f"Fehler beim Laden der Karte: {map_image}")
        st.info("Hinweis: Stellen Sie sicher, dass die gewählte Kombination (z.B. ICON-D2 für ganz Europa) vom DWD unterstützt wird.")

st.markdown("""
---
**Hinweis:** Die Karten zeigen den aktuellsten verfügbaren Modelllauf (Base Time). 
Für zeitliche Vorhersagen (Forecast Steps) müssten die `time`-Parameter der WMS-Schnittstelle erweitert werden.
""")
