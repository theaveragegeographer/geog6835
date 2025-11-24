import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import leafmap.foliumap as leafmap
import requests
from io import BytesIO
import zipfile

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title='Vegetation Dashboard', layout='wide')

st.title('Vegetation Productivity Dashboard')
st.markdown("""
This dashboard visualizes changes in vegetation health (NPP & NDVI) between **2002** and **2022**.
""")

# --- CONFIGURATION & HELPERS ---
# This dictionary maps the ID numbers in your file to real names
FIPS_MAP = {
    4: "Arizona",
    8: "Colorado",
    16: "Idaho",
    32: "Nevada",
    35: "New Mexico",
    49: "Utah",
    56: "Wyoming"
}

st.sidebar.title('Configuration')

# 1. METRIC SELECTOR
metric_type = st.sidebar.radio(
    "Select Metric:",
    ["Net Primary Productivity (NPP)", "Vegetation Index (NDVI)"]
)

# 2. COLOR PICKERS
st.sidebar.write("### Chart Colors")
col1, col2 = st.sidebar.columns(2)
color1 = col1.color_picker('2002', "#86BFE0")
color2 = col2.color_picker('2022', "#C66762")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    # Load Map Shapes
    tiger_url = "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip"
    try:
        r = requests.get(tiger_url)
        z = zipfile.ZipFile(BytesIO(r.content))
        z.extractall("/tmp/tiger_counties")
        gdf = gpd.read_file("/tmp/tiger_counties/tl_2023_us_county.shp")
        gdf['GEOID'] = gdf['GEOID'].astype(str).str.zfill(5)
        gdf = gdf.to_crs(epsg=4326)
    except:
        return gpd.GeoDataFrame(), pd.DataFrame()

    # Load CSV
    try:
        df = pd.read_csv("utah_vegetation_stats.csv")
        df['STATEFP'] = df['STATEFP'].astype(str).str.zfill(2)
        df['GEOID'] = df['GEOID'].astype(str).str.zfill(5)
        
        # Calculate change columns
        df['NPP_Change'] = df['NPP_2022'] - df['NPP_2002']
        df['NDVI_Change'] = df['NDVI_2022'] - df['NDVI_2002']
        
        # Create a "State Name" column for the dropdown
        # We convert the ID (e.g. "49") back to integer to match our dictionary keys
        df['State_Name'] = df['STATEFP'].astype(int).map(FIPS_MAP)
        
        return gdf, df
    except:
        return gpd.GeoDataFrame(), pd.DataFrame()

map_data, stats_data = load_data()

# --- MAIN APP LOGIC ---

if not stats_data.empty and not map_data.empty:
    
    # 3. STATE SELECTOR (Now with Names!)
    # Get list of state names present in the data
    available_states = sorted(stats_data['State_Name'].dropna().unique())
    
    # Set default to "Utah" if available, otherwise first in list
    default_index = available_states.index("Utah") if "Utah" in available_states else 0
    
    selected_state_name = st.sidebar.selectbox(
        'Select a State', 
        available_states, 
        index=default_index
    )

    # Filter data by the Name instead of the ID
    state_stats = stats_data[stats_data['State_Name'] == selected_state_name]
    # Get the ID for the map filter
    selected_state_id = state_stats['STATEFP'].iloc[0]
    state_map = map_data[map_data['STATEFP'] == selected_state_id]
    
    # Merge
    final_data = state_map.merge(state_stats, on='GEOID', how='inner')

    # Configure columns based on metric selection
    if "NPP" in metric_type:
        c1, c2, c_change = 'NPP_2002', 'NPP_2022', 'NPP_Change'
        ylabel = "NPP (Kilo Tonnes)"
    else:
        c1, c2, c_change = 'NDVI_2002', 'NDVI_2022', 'NDVI_Change'
        ylabel = "NDVI Value"

    # --- TABS FOR VISUALIZATION ---
    tab1, tab2 = st.tabs(["🗺️ Map View", "📊 Chart View"])

    with tab1:
        st.subheader(f"{selected_state_name}: {metric_type} Change")
        try:
            m = leafmap.Map(draw_control=False, measure_control=False, fullscreen_control=False)
            m.add_basemap('CartoDB.Positron')
            m.add_data(
                final_data,
                column=c_change,
                scheme="Quantiles",
                cmap="RdYlGn",
                layer_name="Change",
                info_mode="on_click"
            )
            m.to_streamlit(height=550)
        except Exception as e:
            st.error(f"Map Error: {e}")

    with tab2:
        st.subheader(f"County Comparison: 2002 vs 2022")
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Sort by county name
        chart_df = state_stats.sort_values('NAME')
        
        chart_df.plot(
            kind='bar',
            ax=ax,
            x='NAME',
            y=[c1, c2],
            color=[color1, color2],
            width=0.8
        )
        ax.set_ylabel(ylabel)
        ax.set_xticklabels(chart_df['NAME'], rotation=90)
        st.pyplot(fig)

else:
    st.error("Data failed to load. Please check CSV file in GitHub.")
