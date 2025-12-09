import streamlit as st
import leafmap.foliumap as leafmap
import requests

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
        "https://tiles.arcgis.com/tiles/UN2BoTelitQIJWcd/arcgis/rest/services/African_Great_Lakes_Defensive_Military_Geography/MapServer",
    "Western Balkans – Predictive Military Geography": 
        "https://tiles.arcgis.com/tiles/UN2BoTelitQIJWcd/arcgis/rest/services/Predictive_Military_Geography_of_the_ex_Yugoslavia_and_Western_Balkans_WTL1/MapServer",
}

GREG_URL = (
    "https://services7.arcgis.com/iEMmryaM5E3wkdnU/arcgis/rest/services/"
    "GREG_Geo_referencing_of_Ethnic_Groups_/FeatureServer/0"
)

HERETICS_URL = (
    "https://services8.arcgis.com/UN2BoTelitQIJWcd/arcgis/rest/services/"
    "Heretics_Southern_Europe/FeatureServer/0"
)

# Your actual filter fields
GREG_FIELD = "G1SHORTNAM"
HERETICS_FIELD = "MERGE_SRC"


# -------------------------
# Helper functions
# -------------------------

@st.cache_data
def fetch_geojson(feature_url: str):
    """Download full layer as GeoJSON from AGOL FeatureServer."""
    query_url = f"{feature_url}/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
    }
    r = requests.get(query_url, params=params)
    r.raise_for_status()
    return r.json()


def unique_values(geojson_obj, field):
    vals = set()
    for feat in geojson_obj["features"]:
        val = feat["properties"].get(field)
        if val not in [None, ""]:
            vals.add(val)
    return sorted(vals)


def filter_geojson(geojson_obj, field, allowed_values):
    feats = [
        f for f in geojson_obj["features"]
        if f["properties"].get(field) in allowed_values
    ]
    return {**geojson_obj, "features": feats}


# Fetch layers once
greg_geojson = fetch_geojson(GREG_URL)
heretics_geojson = fetch_geojson(HERETICS_URL)

greg_values = unique_values(greg_geojson, GREG_FIELD)
heretics_values = unique_values(heretics_geojson, HERETICS_FIELD)


# -------------------------
# 2) Sidebar controls
# -------------------------

st.sidebar.header("Layer Controls")

# Tile layer selection
selected_tile_name = st.sidebar.radio(
    "Defensive Terrain Tile Layer:",
    list(TILE_LAYERS.keys()),
    index=1
)

tile_opacity = st.sidebar.slider(
    "Tile Layer Opacity:",
    0.1, 1.0, 0.8, 0.05
)

st.sidebar.markdown("---")

# GREG filter
st.sidebar.subheader("GREG – Ethnic Groups")
selected_greg = st.sidebar.multiselect(
    f"Filter by {GREG_FIELD}:",
    greg_values,
    default=greg_values[:10] if len(greg_values) > 10 else greg_values
)

# Heretics filter
st.sidebar.subheader("Heretics – Southern Europe")
selected_heretics = st.sidebar.multiselect(
    f"Filter by {HERETICS_FIELD}:",
    heretics_values,
    default=heretics_values
)

# -------------------------
# 3) MAP
# -------------------------

m = leafmap.Map(center=[30, 10], zoom=2)

# Tile layer
tile_url = TILE_LAYERS[selected_tile_name]
if tile_url:
    m.add_tile_layer(
        url=tile_url,
        name=selected_tile_name,
        opacity=tile_opacity,
        attribution="ArcGIS Online"
    )

# Filter + add GREG
if selected_greg:
    greg_filtered = filter_geojson(greg_geojson, GREG_FIELD, selected_greg)
    m.add_geojson(greg_filtered, layer_name="GREG (filtered)")

# Filter + add Heretics
if selected_heretics:
    heretics_filtered = filter_geojson(heretics_geojson, HERETICS_FIELD, selected_heretics)
    m.add_geojson(heretics_filtered, layer_name="Heretics (filtered)")

# Adjust view
m.zoom_to_layers()

# Render
m.to_streamlit(height=700)

st.caption(
    "Tile layers = your predictive/defensive military geography from ArcGIS Online. "
    "Use the filters to explore how ethnic and heretical groups in different historical periods "
    "map onto defensible terrain."
)
