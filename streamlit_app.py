import streamlit as st
import folium
from streamlit_folium import folium_static

# Seiteneinstellungen für Breitbild
st.set_page_config(page_title="DWD Modellkarten", layout="wide")

st.title("🛰️ DWD Modellkarten (ICON)")

# --- Sidebar / Radio Button Menü ---
st.sidebar.header("Navigation")

# 1. Region wählen
region_choice = st.sidebar.radio(
    "Region auswählen",
    ["Mitteleuropa", "Deutschland", "Berlin/Brandenburg"]
)

# 2. Modell wählen
model_choice = st.sidebar.radio(
    "Wettermodell",
    ["ICON-D2 (Hochauflösend)", "ICON-EU (Europa)"]
)

# 3. Parameter wählen
param_choice = st.sidebar.radio(
    "Parameter",
    ["2m Temperatur", "Niederschlagsrate", "Windböen"]
)

# --- Konfiguration der Layer & Koordinaten ---

# Koordinaten-Mapping [Lat, Lon, Zoom]
region_map = {
    "Mitteleuropa": [50.0, 12.5, 5],
    "Deutschland": [51.1, 10.4, 6],
    "Berlin/Brandenburg": [52.4, 13.2, 8]
}

# Mapping für DWD WMS Layer Namen
# Hinweis: Die Namen entsprechen der Struktur auf https://maps.dwd.de
layer_prefix = "icon-d2" if "D2" in model_choice else "icon-eu"
param_suffix = {
    "2m Temperatur": "2m_temperature",
    "Niederschlagsrate": "total_precipitation",
    "Windböen": "maximum_wind_gust_10m"
}

# Vollständiger Layer-Pfad für den DWD Geoserver
# Beispiel: dwd:icon-d2_germany_single_level_elements_2m_temperature
dwd_layer = f"dwd:{layer_prefix}_germany_single_level_elements_{param_suffix[param_choice]}"
if "EU" in model_choice:
    dwd_layer = f"dwd:{layer_prefix}_europe_single_level_elements_{param_suffix[param_choice]}"

# --- Karten-Erstellung ---

st.subheader(f"Karte: {param_choice} ({model_choice}) - {region_choice}")

# Karte initialisieren
m = folium.Map(
    location=[region_map[region_choice][0], region_map[region_choice][1]],
    zoom_start=region_map[region_choice][2],
    tiles="cartodbpositron", # Dezente Hintergrundkarte
    control_scale=True
)

# WMS Layer vom DWD hinzufügen
wms_url = "https://maps.dwd.de/geoserver/dwd/wms"

folium.WmsTileLayer(
    url=wms_url,
    layers=dwd_layer,
    fmt="image/png",
    transparent=True,
    version="1.3.0",
    name=f"DWD {param_choice}",
    overlay=True,
    control=True,
    opacity=0.7
).add_to(m)

# Karte in Streamlit anzeigen
folium_static(m, width=1200, height=700)

# --- Legende (Optional: Dynamisch vom DWD Server laden) ---
st.sidebar.markdown("---")
st.sidebar.info("Die Daten werden in Echtzeit vom DWD Geoserver geladen.")

# Legenden-Grafik einbinden
legend_url = f"{wms_url}?REQUEST=GetLegendGraphic&VERSION=1.3.0&FORMAT=image/png&LAYER={dwd_layer}"
st.sidebar.image(legend_url, caption="Legende / Farbskala")
