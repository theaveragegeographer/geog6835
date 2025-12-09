import streamlit as st
import leafmap.foliumap as leafmap
import requests

# -------------------------
# Page config
# -------------------------

st.set_page_config(layout="wide", page_title="Geopolitics & Heretics Dashboard")
st.title("Geopolitics, Ethnic Groups, and Military Geography")

st.markdown(
    "Use the controls on the left to toggle defensive terrain layers and "
    "filter ethnoreligious / cultural feature layers (GREG)."
)

# -------------------------
# 1) Your AGOL layers
# -------------------------

TILE_LAYERS = {
    "None": None,
    "African Great Lakes – Defensive Military Geography": (
        "https://tiles.arcgis.com/tiles/UN2BoTelitQIJWcd/arcgis/rest/services/"
        "African_Great_Lakes_Defensive_Military_Geography/MapServer"
    ),
    "Western Balkans – Predictive Military Geography": (
        "https://tiles.arcgis.com/tiles/UN2BoTelitQIJWcd/arcgis/rest/services/"
        "Predictive_Military_Geography_of_the_ex_Yugoslavia_and_Western_Balkans_WTL1/MapServer"
    ),
}

GREG_URL = (
    "https://services7.arcgis.com/iEMmryaM5E3wkdnU/arcgis/rest/services/"
    "GREG_Geo_referencing_of_Ethnic_Groups_/FeatureServer/0"
)

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
    except Exception as e:
        st.error(f"Error connecting to {feature_url}: {e}")
        return {"type": "FeatureCollection", "features": []}

    if not r.ok:
        st.error(
            f"Error fetching layer from {feature_url}\n"
            f"Status code: {r.status_code}"
        )
        return {"type": "FeatureCollection", "features": []}

    try:
        return r.json()
    except Exception as e:
        st.error(f"Error parsing JSON from {feature_url}: {e}")
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
