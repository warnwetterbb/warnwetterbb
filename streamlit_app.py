"""
WarnWetterBB - Professional Weather Dashboard
Dieses Modul stellt eine Verbindung zu den WMS-Servern des DWD und EOX her,
um Wettermodelle und Live-Radardaten auf Satellitenbildern zu visualisieren.
"""

import streamlit as st
import requests
from io import BytesIO
from PIL import Image

# ==========================================
# 1. KONFIGURATION UND DATEN
# ==========================================

# Regionale Bounding Boxes (EPSG:4326)
BBOX_MAP = {
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

# Parameter Mapping für den DWD Geoserver
MODELS = {"ICON-D2 (Regional)": "icon-d2_germany", "ICON-EU (Europa)": "icon-eu_europe"}
PARAMETERS = {
    "2m Temperatur": "2m_temperature",
    "Niederschlagsrate": "total_precipitation",
    "Windböen": "maximum_wind_gust_10m"
}

# ==========================================
# 2. HILFSFUNKTIONEN (CORE LOGIC)
# ==========================================

def fetch_wms_image(url: str, params: dict, timeout: int = 15) -> Image.Image | str:
    """
    Universelle Funktion, um Bilder von einem WMS-Server (Web Map Service) herunterzuladen.
    Gibt ein PIL-Image zurück, oder einen String mit der Fehlermeldung.
    """
    try:
        response = requests.get(url, params=params, timeout=timeout)
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            return Image.open(BytesIO(response.content))
        return f"WMS-Fehler: Server meldet Status {response.status_code}."
    except requests.exceptions.RequestException as e:
        return f"Verbindungsfehler: {str(e)}"
    except Exception as e:
        return f"Unerwarteter Fehler bei der Bildverarbeitung: {str(e)}"

@st.cache_data(ttl=300) # 5 Minuten Cache für Live-Radar
def create_radar_composite(bbox: str) -> Image.Image | str:
    """
    Lädt das Sentinel-2 Satellitenbild und das DWD Regenradar herunter,
    wandelt beide in RGBA um und legt das transparente Radar über das Satellitenbild.
    """
    # 1. Satellitenbild (Background)
    sat_url = "https://services.eox.at/wms/"
    sat_params = {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
        "LAYERS": "s2cloudless-2020", "STYLES": "", "BBOX": bbox,
        "WIDTH": "1200", "HEIGHT": "800", "CRS": "EPSG:4326", "FORMAT": "image/jpeg"
    }
    
    # 2. DWD Regenradar (Foreground - Transparent)
    rad_url = "https://maps.dwd.de/geoserver/dwd/wms"
    rad_params = {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
        "LAYERS": "dwd:RX-Produkt", "STYLES": "", "BBOX": bbox,
        "WIDTH": "1200", "HEIGHT": "800", "CRS": "EPSG:4326",
        "FORMAT": "image/png", "TRANSPARENT": "TRUE"
    }
    
    sat_img = fetch_wms_image(sat_url, sat_params)
    rad_img = fetch_wms_image(rad_url, rad_params)
    
    # Fehlerprüfung
    if isinstance(sat_img, str): return f"Satelliten-Fehler: {sat_img}"
    if isinstance(rad_img, str): return f"Radar-Fehler: {rad_img}"
    
    # Composite erstellen (Transparenz erhalten)
    try:
        sat_rgba = sat_img.convert("RGBA")
        rad_rgba = rad_img.convert("RGBA")
        composite = Image.alpha_composite(sat_rgba, rad_rgba)
        return composite
    except Exception as e:
        return f"Fehler beim Zusammenfügen der Bilder: {str(e)}"

@st.cache_data(ttl=1800) # 30 Min Cache für Modelle
def get_model_map(layer_name: str, bbox: str) -> Image.Image | str:
    """Lädt die statische Modellkarte des DWD herunter."""
    url = "https://maps.dwd.de/geoserver/dwd/wms"
    params = {
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
        "LAYERS": layer_name, "STYLES": "", "BBOX": bbox,
        "WIDTH": "1200", "HEIGHT": "800", "CRS": "EPSG:4326",
        "FORMAT": "image/png", "TRANSPARENT": "FALSE"
    }
    return fetch_wms_image(url, params)

# ==========================================
# 3. FRONTEND / UI (STREAMLIT)
# ==========================================

def main():
    st.set_page_config(page_title="WarnWetter Dashboard", page_icon="🌤️", layout="wide")
    st.title("🛰️ Professional Weather Dashboard")
    st.markdown("Basierend auf OpenData des **Deutschen Wetterdienstes (DWD)** und **Sentinel-2**.")

    # --- Sidebar ---
    st.sidebar.header("Menü & Navigation")
    
    app_mode = st.sidebar.radio("Modus:", ["🌧️ Live-Regenradar", "🗺️ DWD Modellkarten"])
    region_choice = st.sidebar.radio("Region / Bundesland:", list(BBOX_MAP.keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.info("Entwickelt mit Python & Streamlit. Daten via WMS.")

    # --- Ansicht: Regenradar ---
    if app_mode == "🌧️ Live-Regenradar":
        st.subheader(f"Echtzeit-Radar über {region_choice}")
        
        # Legend-Info (Statisch, da Streamlit die PNG-Pixel nicht ändern kann)
        with st.expander("ℹ️ Info zur Radar-Farbskala (Reflektivität)"):
            st.markdown("""
            *Das DWD RX-Produkt liefert die Reflektivität in dBZ (Dezibel relativ zu Z).*
            * **Blau/Hellblau (~15-20 dBZ):** Leichter Regen oder Nieselregen.
            * **Grün/Gelb (~30-40 dBZ):** Mäßiger bis starker Regen.
            * **Rot/Magenta (> 45 dBZ):** Sehr starker Regen, Hagelgefahr oder Gewitter.
            """)
        
        with st.spinner(f"Verarbeite Satelliten- und Radardaten für {region_choice}..."):
            radar_image = create_radar_composite(BBOX_MAP[region_choice])
            
            if isinstance(radar_image, Image.Image):
                st.image(radar_image, width="stretch", caption="Live-Radar (RX) auf wolkenfreiem Satellitenbild")
            else:
                st.error("Bild konnte nicht geladen werden.")
                st.code(radar_image)

    # --- Ansicht: Wettermodelle ---
    elif app_mode == "🗺️ DWD Modellkarten":
        st.subheader(f"Numerische Vorhersage - {region_choice}")
        
        # Modell-Steuerung in zwei Spalten
        col1, col2 = st.columns(2)
        with col1:
            sel_model = st.radio("Modell:", list(MODELS.keys()))
        with col2:
            sel_param = st.radio("Parameter:", list(PARAMETERS.keys()))
            
        layer = f"dwd:{MODELS[sel_model]}_single_level_elements_{PARAMETERS[sel_param]}"
        
        with st.spinner("Frage DWD Geoserver ab..."):
            model_image = get_model_map(layer, BBOX_MAP[region_choice])
            
            if isinstance(model_image, Image.Image):
                st.image(model_image, width="stretch", caption=f"Modelllauf: {sel_model} | {sel_param}")
                
                # Legende vom DWD laden
                st.markdown("### Farbskala")
                legend_url = f"https://maps.dwd.de/geoserver/dwd/wms?service=WMS&request=GetLegendGraphic&format=image/png&layer={layer}"
                st.image(legend_url)
            else:
                st.error("Kartenlayer nicht verfügbar.")
                st.warning("Info: ICON-D2 Daten sind auf Deutschland und angrenzendes Ausland beschränkt.")
                st.code(model_image)

if __name__ == "__main__":
    main()
