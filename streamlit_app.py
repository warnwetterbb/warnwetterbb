import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from PIL import Image

# --- Seiteneinstellungen ---
st.set_page_config(page_title="WarnWetter Dashboard", layout="wide")

st.title("🛰️ Profi Wetter-Dashboard")

# --- Bounding Boxes für Deutschland & alle 16 Bundesländer ---
bbox_map = {
    "Deutschland": "5.5,47.0,15.5,55.5",
    "Baden-Württemberg": "7.5,47.5,10.5,49.8",
    "Bayern": "8.9,47.2,13.9,50.6",
    "Berlin": "13.1,52.3,13.8,52.7",
    "Brandenburg": "11.2,51.3,14.8,53.6",
    "Bremen": "8.4,53.0,9.0,53.6",
    "Hamburg": "9.7,53.3,10.4,53.8",
    "Hessen": "7.7,49.3,10.3,51.7",
    "Mecklenburg-Vorpommern": "10.5,53.1,14.4,54.7",
    "Niedersachsen": "6.6,51.2,11.6,54.0",
    "Nordrhein-Westfalen": "5.8,50.3,9.5,52.6",
    "Rheinland-Pfalz": "6.1,48.9,8.6,51.0",
    "Saarland": "6.3,49.1,7.5,49.7",
    "Sachsen": "11.8,50.1,15.1,51.7",
    "Sachsen-Anhalt": "10.5,50.9,13.2,53.1",
    "Schleswig-Holstein": "7.8,53.3,11.4,55.1",
    "Thüringen": "9.8,50.2,12.7,51.7"
}

# --- Sidebar: Hauptsteuerung (Nur Radio-Buttons) ---
st.sidebar.header("Navigation")

app_mode = st.sidebar.radio(
    "Ansicht wählen:",
    ["🌧️ Live-Regenradar", "🗺️ DWD Modellkarten"]
)

region_choice = st.sidebar.radio(
    "Region wählen:",
    list(bbox_map.keys())
)

st.sidebar.markdown("---")

# ==========================================
# ANSICHT 1: LIVE REGENRADAR
# ==========================================
if app_mode == "🌧️ Live-Regenradar":
    st.subheader(f"Live-Radar über echtem Satellitenbild - {region_choice}")
    
    # 1. Farbrad-Tabelle (Interaktiv)
    st.markdown("### Radar-Farben & Legende anpassen")
    st.info("Da das DWD-Radarbild ein serverseitig gerendertes PNG ist, ändert diese Tabelle das Bild nicht live. Sie dient als anpassbare interaktive Legende für dein Dashboard.")
    
    # Initiale Daten für die Tabelle
    if "radar_colors" not in st.session_state:
        st.session_state.radar_colors = pd.DataFrame({
            "Intensität": ["Leicht (Niesel)", "Mittel (Regen)", "Stark (Schauer)", "Extrem (Hagel/Sturm)"],
            "Reflektivität (dBZ)": [15, 30, 45, 55],
            "Farbe": ["#00BFFF", "#32CD32", "#FFD700", "#FF0000"]
        })

    # Interaktive Tabelle mit Farbrad (Color Picker)
    edited_df = st.data_editor(
        st.session_state.radar_colors,
        column_config={
            "Farbe": st.column_config.ColorColumn(
                "Farbe (Farbrad)",
                help="Klicke, um die Farbe per Farbrad zu ändern",
            ),
            "Reflektivität (dBZ)": st.column_config.NumberColumn(
                "Reflektivität (dBZ)",
                min_value=0, max_value=80, step=1
            )
        },
        hide_index=True,
        use_container_width=True
    )
    st.session_state.radar_colors = edited_df

    # 2. Bilder abrufen und kombinieren
    @st.cache_data(ttl=300) # Nur 5 Min Cache, da Regenradar live ist
    def get_radar_map(bbox):
        # Basis-Satellitenbild (Sentinel-2 Cloudless via EOX WMS)
        sat_url = "https://services.eox.at/wms/"
        sat_params = {
            "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
            "LAYERS": "s2cloudless-2020", "STYLES": "", "BBOX": bbox,
            "WIDTH": "1200", "HEIGHT": "800", "CRS": "EPSG:4326",
            "FORMAT": "image/jpeg"
        }
        
        # DWD Live-Regenradar (RX-Produkt - Nationales Komposit)
        rad_url = "https://maps.dwd.de/geoserver/dwd/wms"
        rad_params = {
            "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
            "LAYERS": "dwd:RX-Produkt", "STYLES": "", "BBOX": bbox,
            "WIDTH": "1200", "HEIGHT": "800", "CRS": "EPSG:4326",
            "FORMAT": "image/png", "TRANSPARENT": "TRUE"
        }
        
        try:
            # Beide Bilder anfragen
            sat_res = requests.get(sat_url, params=sat_params, timeout=10)
            rad_res = requests.get(rad_url, params=rad_params, timeout=10)
            
            if sat_res.status_code == 200 and rad_res.status_code == 200:
                # Bilder in Pillow (PIL) laden und in RGBA umwandeln für Transparenz
                sat_img = Image.open(BytesIO(sat_res.content)).convert("RGBA")
                rad_img = Image.open(BytesIO(rad_res.content)).convert("RGBA")
                
                # Bilder übereinanderlegen (Alpha Composite)
                combined = Image.alpha_composite(sat_img, rad_img)
                return combined
            else:
                return f"Fehler bei der API: Satellit={sat_res.status_code}, Radar={rad_res.status_code}"
        except Exception as e:
            return str(e)

    with st.spinner("Lade Satellitendaten und Live-Radar..."):
        radar_image = get_radar_map(bbox_map[region_choice])
        
        if isinstance(radar_image, Image.Image):
            st.image(radar_image, width="stretch", caption="Echtzeit Regenradar auf Sentinel-2 Satellitenbild")
        else:
            st.error(f"Konnte Radar nicht laden: {radar_image}")

# ==========================================
# ANSICHT 2: DWD MODELLKARTEN
# ==========================================
elif app_mode == "🗺️ DWD Modellkarten":
    st.subheader(f"Wettermodell - {region_choice}")
    
    model_choice = st.sidebar.radio(
        "Modell wählen:",
        ["ICON-D2 (Feinmaschig)", "ICON-EU (Europa)"]
    )

    param_choice = st.sidebar.radio(
        "Parameter wählen:",
        ["2m Temperatur", "Niederschlagsrate", "Windböen"]
    )
    
    model_key = "icon-d2_germany" if "D2" in model_choice else "icon-eu_europe"
    param_key = {
        "2m Temperatur": "2m_temperature",
        "Niederschlagsrate": "total_precipitation",
        "Windböen": "maximum_wind_gust_10m"
    }
    layer_name = f"dwd:{model_key}_single_level_elements_{param_key[param_choice]}"

    @st.cache_data(ttl=600)
    def get_static_map(layer, bbox):
        wms_url = "https://maps.dwd.de/geoserver/dwd/wms"
        params = {
            "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
            "LAYERS": layer, "STYLES": "", "BBOX": bbox,
            "WIDTH": "1200", "HEIGHT": "800", "CRS": "EPSG:4326",
            "FORMAT": "image/png", "TRANSPARENT": "FALSE"
        }
        try:
            response = requests.get(wms_url, params=params, timeout=15)
            if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
                return response.content
            return f"Server meldet {response.status_code}"
        except Exception as e:
            return str(e)

    with st.spinner("Lade Karte..."):
        map_result = get_static_map(layer_name, bbox_map[region_choice])
        if isinstance(map_result, bytes):
            st.image(map_result, width="stretch")
            
            # Original DWD Legende
            st.sidebar.markdown("---")
            st.sidebar.write("**Modell-Legende:**")
            st.sidebar.image(f"https://maps.dwd.de/geoserver/dwd/wms?service=WMS&request=GetLegendGraphic&format=image/png&layer={layer_name}")
        else:
            st.error(f"Fehler: {map_result}")
            st.warning("Hinweis: Manche D2-Layer sind für Boxen außerhalb Deutschlands fehlerhaft.")
