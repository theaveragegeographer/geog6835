import streamlit as st
import leafmap.foliumap as leafmap
import requests

# -------------------------
# Page config
# -------------------------

st.set_page_config(layout="wide", page_title="Geopolitics Dashboard")
st.title("Geopolitics, Ethnic Groups, and Military Geography")

st.markdown(
    "Use the controls on the left to toggle defensive terrain layers and "
    "filter ethnoreligious / cultural feature layers (GREG)."
)

# -------------------------
# 1) AGOL layers
# -------------------------

TILE_LAYERS = {
    "None": None,
    "African Great Lakes – Defensive Military Geography": (
        "https://tiles.arcgis.com/tiles/UN2BoTelitQIJWcd/arcgis/rest/services/"
        "African_Great_Lakes_Defensive_Military_Geography/MapServer/tile/{z}/{y}/{x}"
    ),
    "Western Balkans – Predictive Military Geography": (
        "https://tiles.arcgis.com/tiles/UN2BoTelitQIJWcd/arcgis/rest/services/"
        "Predictive_Military_Geography_of_the_ex_Yugoslavia_and_Western_Balkans_WTL1/MapServer/tile/{z}/{y}/{x}"
    ),
}


GREG_FIELD = "G1SHORTNAM"  # field to filter on


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
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error fetching {feature_url}: {e}")
        return {"type": "FeatureCollection", "features": []}


def unique_values(geojson_obj, field):
    vals = set()
    for feat in geojson_obj.get("features", []):
        props = feat.get("properties", {})
        val = props.get(field)
        if val not in [None, ""]:
            vals.add(val)
    return sorted(vals)


def filter_geojson(geojson_obj, field, allowed_values):
    feats = [
        f
        for f in geojson_obj.get("features", [])
        if f.get("properties", {}).get(field) in allowed_values
    ]
    return {**geojson_obj, "features": feats}


# -------------------------
# 3) Fetch GREG once
# -------------------------

greg_geojson = fetch_geojson(GREG_URL)
greg_values = unique_values(greg_geojson, GREG_FIELD)

# -------------------------
# 4) Sidebar controls
# -------------------------

st.sidebar.header("Layer Controls")

# Tile layer selection
selected_tile_name = st.sidebar.radio(
    "Defensive Terrain Tile Layer:",
    list(TILE_LAYERS.keys()),
    index=1,  # default to African Great Lakes
)

tile_opacity = st.sidebar.slider(
    "Tile Layer Opacity:",
    0.1,
    1.0,
    0.8,
    0.05,
)

st.sidebar.markdown("---")

# GREG filter
st.sidebar.subheader("GREG – Ethnic Groups")
if greg_values:
    selected_greg = st.sidebar.multiselect(
        f"Filter by {GREG_FIELD}:",
        greg_values,
        default=greg_values[:10] if len(greg_values) > 10 else greg_values,
    )
else:
    st.sidebar.warning("Could not load GREG groups.")
    selected_greg = []


# -------------------------
# 5) Map
# -------------------------

# Start with a broad global view; user can pan/zoom
m = leafmap.Map(center=[20, 10], zoom=2)

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

m.to_streamlit(height=700)

st.caption(
    "Tile layers = your predictive/defensive military geography from ArcGIS Online. "
    "GREG groups (G1SHORTNAM) are filtered in the sidebar and overlaid on top. "
    "Pan and zoom the map to explore how ethnic geographies align with defensible terrain."
)
