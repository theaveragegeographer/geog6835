import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import leafmap.foliumap as leafmap
import requests
from io import BytesIO
import zipfile

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title='Utah Vegetation Dashboard', layout='wide')

st.title('Utah Vegetation Analysis Dashboard')
st.markdown("""
This dashboard visualizes changes in vegetation health between **2002** and **2022**.
Use the sidebar to switch between **NPP** (Productivity) and **NDVI** (Greenness).
""")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title('Configuration')

# INTERACTIVE ELEMENT 1: Radio Button (Metric Selector)
metric_type = st.sidebar.radio(
    "Select Metric to Analyze:",
    ["Net Primary Productivity (NPP)", "Vegetation Index (NDVI)"]
)

# INTERACTIVE ELEMENT 2: Color Pickers
st.sidebar.write("### Chart Colors")
col1, col2 = st.sidebar.columns(2)
color1 = col1.color_picker('2002', "#86BFE0")
color2 = col2.color_picker('2022', "#C66762")

# --- DATA LOADING (Cached) ---
@st.cache_data
def load_data():
    # 1. Load Map Shapes
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

    # 2. Load CSV Data
    try:
        df = pd.read_csv("utah_vegetation_stats.csv")
        df['STATEFP'] = df['STATEFP'].astype(str).str.zfill(2)
        df['GEOID'] = df['GEOID'].astype(str).str.zfill(5)
        
        # Calculate Changes for both metrics
        df['NPP_Change'] = df['NPP_2022'] - df['NPP_2002']
        df['NDVI_Change'] = df['NDVI_2022'] - df['NDVI_2002']
        
        return gdf, df
    except:
        return gpd.GeoDataFrame(), pd.DataFrame()

map_data, stats_data = load_data()

# --- MAIN APP LOGIC ---

if not stats_data.empty and not map_data.empty:
    
    # 1. Determine which columns to use based on Radio Button
    if "NPP" in metric_type:
        col_02 = 'NPP_2002'
        col_22 = 'NPP_2022'
        col_change = 'NPP_Change'
        label = "NPP (Kilo Tonnes)"
    else:
        col_02 = 'NDVI_2002'
        col_22 = 'NDVI_2022'
        col_change = 'NDVI_Change'
        label = "NDVI (Index Value)"

    # INTERACTIVE ELEMENT 3: State Dropdown
    state_list = sorted(stats_data['STATEFP'].unique())
    selected_state = st.sidebar.selectbox('Select State ID', state_list)

    # Filter Data
    state_stats = stats_data[stats_data['STATEFP'] == selected_state]
    state_map = map_data[map_data['STATEFP'] == selected_state]
    
    # Merge for Mapping
    final_data = state_map.merge(state_stats, on='GEOID', how='inner')

    # LAYOUT: Create two tabs for organized visualization
    tab1, tab2 = st.tabs(["🗺️ Geospatial Map", "📊 Statistical Chart"])

    with tab1:
        st.subheader(f"Change in {metric_type} (2002-2022)")
        m = leafmap.Map(draw_control=False, measure_control=False, fullscreen_control=False)
        m.add_basemap('CartoDB.Positron')
        
        try:
            m.add_data(
                final_data,
                column=col_change,
                scheme="Quantiles",
                cmap="RdYlGn",
                layer_name=f"{metric_type} Change",
                info_mode="on_click"
            )
            m.to_streamlit(height=550)
        except Exception as e:
            st.error(f"Map Error: {e}")

    with tab2:
        st.subheader(f"Comparison: 2002 vs 2022")
        
        # Sort data for cleaner chart
        chart_df = state_stats.sort_values('NAME')
        
        fig, ax = plt.subplots(figsize=(10, 5))
        chart_df.plot(
            kind='bar',
            ax=ax,
            x='NAME',
            y=[col_02, col_22],
            color=[color1, color2],
            width=0.8
        )
        ax.set_ylabel(label)
        ax.set_title(f"{metric_type} by County")
        ax.set_xticklabels(chart_df['NAME'], rotation=90)
        st.pyplot(fig)
        
        st.write("### Raw Data Statistics")
        st.dataframe(state_stats[['NAME', col_02, col_22, col_change]].describe())

else:
    st.error("Data could not load. Please check 'utah_vegetation_stats.csv' is in GitHub.")
