import streamlit as st
import leafmap.foliumap as leafmap
import requests

# -------------------------
# Page config
# -------------------------

st.set_page_config(layout="wide", page_title="Geopolitics & Heretics Dashboard")
st.title("Geopolitics, Heretics, and Military Geography")

st.markdown(
    "Use the controls on the left to toggle defensive terrain layers and "
    "filter ethnoreligious / cultural feature layers."
)

# -------------------------
# 1) Your AGOL layers
# -------------------------

TILE_LAYERS = {
    "None": None,
    "African Great Lakes – Defensive Military Geography":
        "https://tiles.arcgis.com/tiles/UN2BoTelitQIJWcd/arcgis/rest/services/"
        "African_Great_Lakes_Defensive_Military_Geography/MapServer",
    "Western Balkans – Predictive Military Geography":
        "https://tiles.arcgis.com/tiles/UN2BoTelitQIJWcd/arcgis/rest/services/"
        "Predictive_Military_Geography_of_the_ex_Yugoslavia_and_Western_Balkans_WTL1/MapServer",
}

GREG_URL = (
    "https://services7.arcgis.com/iEMmryaM5E3wkdnU/arcgis/rest/services/"
    "GREG_Geo_referencing_of_Ethnic_Groups_/FeatureServer/0"
)

HERETICS_URL = (
    "https://services8.arcgis.com/UN2BoTelitQIJWcd/arcgis/rest/services/"
    "Heretics_Southern_Europe/FeatureServer/0"
)

# Field used for GREG filtering
GREG_FIELD = "G1SHORTNAM"


# -------------------------
# 2) Helper functions
# -------------------------

@st.cache_data
def fetch_geojson(feature_url: str):
    """Download full layer as GeoJSON from an AGOL FeatureServer layer."""
    query_url = f"{feature_url}/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
    }

    try:
        r = requests.get(query_url, params=params, timeout=30)
    except Exception as e:
        st.error(f"Error connecting to {feature_url}: {e}")
        return {"type": "FeatureCollection", "features": []}

    if not r.ok:
        st.error(
            f"Error fetching layer from {feature_url}\n"
            f"Status code: {r.status_code}"
        )
        return {"type": "FeatureCollection", "features": []}

    return r.json()


def unique_values(geojson_obj, field):
    vals = set()
    for feat in geojson_obj.get("features", []):
        val = feat.get("properties", {}).get(field)
        if val not in [None, ""]:
            vals.add(val)
    return sorted(vals)


def filter_geojson(geojson_obj, field, allowed_values):
    feats = [
        f for f in geojson_obj.get("features", [])
        if f.get("properties", {}).get(field) in allowed_values
    ]
    return {**geojson_obj, "features": feats}


# -------------------------
# 3) Fetch GREG once (Heretics will be added directly as a layer)
# -------------------------

greg_geojson = fetch_geojson(GREG_URL)
greg_values = unique_values(greg_geojson, GREG_FIELD)


# -------------------------
# 4) Sidebar controls
# -------------------------

st.sidebar.header("Layer Controls")

# Tile layer choice
selected_tile_name = st.sidebar.radio(
    "Defensive Terrain Tile Layer:",
    list(TILE_LAYERS.keys()),
    index=1,  # default to African Great Lakes
)

tile_opacity = st.sidebar.slider(
    "Tile Layer Opacity:",
    0.1, 1.0, 0.8, 0.05
)

st.sidebar.markdown("---")

# GREG filter
st.sidebar.subheader("GREG – Ethnic Groups")

if greg_values:
    default_greg = greg_values[:10] if len(greg_values) > 10 else greg_values
    selected_greg = st.sidebar.multiselect(
        f"Filter by {GREG_FIELD}:",
        greg_values,
        default=default_greg,
    )
else:
    st.sidebar.warning("Could not load GREG groups; showing none.")
    selected_greg = []

# Heretics toggle (no filtering for now)
st.sidebar.subheader("Heretics – Southern Europe")
show_heretics = st.sidebar.checkbox("Show Heretics layer", value=True)


# -------------------------
# 5) Map construction
# -------------------------

m = leafmap.Map(center=[30, 10], zoom=2)

# Tile layer
tile_url = TILE_LAYERS[selected_tile_name]
if tile_url:
    m.add_tile_layer(
        url=tile_url,
        name=selected_tile_name,
        opacity=tile_opacity,
        attribution="ArcGIS Online",
    )

# Filter + add GREG
if selected_greg:
    greg_filtered = filter_geojson(greg_geojson, GREG_FIELD, selected_greg)
    if greg_filtered["features"]:
        m.add_geojson(greg_filtered, layer_name="GREG (filtered)")

# Add Heretics as a normal AGOL feature layer
if show_heretics:
    m.add_arcgis_feature_layer(
        HERETICS_URL,
        layer_name="Heretics – Southern Europe",
    )

# Adjust view and render
m.zoom_to_layers()
m.to_streamlit(height=700)

st.caption(
    "Tile layers = your predictive/defensive military geography from ArcGIS Online. "
    "GREG is filtered by short group name (G1SHORTNAM). "
    "Heretical communities in Southern Europe are shown as an overlay. "
    "Use the sidebar and map layer controls to explore how groups map onto defensible terrain."
)
