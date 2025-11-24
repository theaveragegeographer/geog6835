import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import leafmap.foliumap as leafmap
import requests
from io import BytesIO
import zipfile

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title='NPP Dashboard', layout='wide')

st.title('Net Primary Productivity (NPP) Dashboard')
st.write('This dashboard visualizes Net Primary Productivity (NPP) changes over time. ' 
         'Select a state to see the difference between 2002 and 2022.')

st.info("Note: This app downloads US Census map data to run. It may take a moment to load initially.")

# --- SIDEBAR SETUP ---
st.sidebar.title('Configuration')

# Color pickers for the chart
col1, col2 = st.sidebar.columns(2)
nh_color = col1.color_picker('Pick 2002 Color', "#86BFE0")
sh_color = col2.color_picker('Pick 2022 Color', "#C66762")

# --- DATA LOADING FUNCTIONS ---

@st.cache_data
def load_tiger_counties():
    """
    Downloads and caches the US Census County Shapefiles.
    This prevents the app from re-downloading the map every time you click something.
    """
    tiger_url = "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip"
    
    with st.spinner("Downloading US Map Data..."):
        try:
            r = requests.get(tiger_url)
            z = zipfile.ZipFile(BytesIO(r.content))
            # Extract to a temporary folder
            z.extractall("/tmp/tiger_counties")
            
            # Read the shapefile
            gdf = gpd.read_file("/tmp/tiger_counties/tl_2023_us_county.shp")
            # Ensure GEOID is a 5-digit string (e.g., "01001")
            gdf['GEOID'] = gdf['GEOID'].astype(str).str.zfill(5)
            # Convert to standard latitude/longitude format
            gdf = gdf.to_crs(epsg=4326)
            return gdf
        except Exception as e:
            st.error(f"Error loading map data: {e}")
            return gpd.GeoDataFrame()

@st.cache_data
def load_npp_data():
    """
    Loads the CSV file from your GitHub repository.
    IMPORTANT: The file must be named exactly 'us_counties_npp_change_2002_2022.csv'
    """
    csv_filename = "us_counties_npp_change_2002_2022.csv"
    
    try:
        df = pd.read_csv(csv_filename)
        # Clean up IDs to match the map
        df = df[['NAME', 'GEOID', 'STATEFP', '2002', '2022', 'NPP_Change']]
        df['STATEFP'] = df['STATEFP'].astype(str).str.zfill(2)
        df['GEOID'] = df['GEOID'].astype(str).str.zfill(5)
        return df
    except FileNotFoundError:
        st.error(f"Could not find the file '{csv_filename}'. Please make sure you uploaded it to GitHub!")
        return pd.DataFrame()

# --- MAIN APP LOGIC ---

# 1. Load the data
map_data = load_tiger_counties()
npp_data = load_npp_data()

# Only proceed if data loaded successfully
if not npp_data.empty and not map_data.empty:
    
    # 2. State Selection
    available_states = npp_data['STATEFP'].unique()
    selected_state = st.sidebar.selectbox('Select a State ID', available_states)

    # Filter data for the selected state
    state_npp_data = npp_data[npp_data['STATEFP'] == selected_state]
    state_map_data = map_data[map_data['STATEFP'] == selected_state]

    # Merge the map shapes with the NPP data
    final_data = state_map_data.merge(state_npp_data, on='GEOID', how='left')

    # 3. Display Statistics
    st.sidebar.subheader("State Statistics")
    st.sidebar.dataframe(state_npp_data.describe())

    # 4. Map Visualization
    st.write("## 1. Map: NPP Change (2002-2022)")
    
    try:
        m = leafmap.Map(draw_control=False, measure_control=False, fullscreen_control=False)
        m.add_basemap('CartoDB.Positron')
        
        m.add_data(
            final_data,
            column="NPP_Change",
            scheme="Quantiles",
            cmap="RdYlGn",
            layer_name="NPP Change",
            info_mode="on_click"
        )
        m.to_streamlit(height=500)
    except Exception as e:
        st.warning(f"Map could not render: {e}")

    # 5. Chart Visualization
    st.write("## 2. Chart: Comparison by County")
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    # Sort data by county name for a cleaner chart
    chart_data = state_npp_data.sort_values('NAME')
    
    # Plot the bar chart
    chart_data.plot(
        kind='bar', 
        ax=ax, 
        color=[nh_color, sh_color], 
        x='NAME', 
        y=['2002', '2022'], 
        width=0.8
    )
    
    ax.set_ylabel('NPP (Kilo tonnes)')
    ax.set_xlabel('County')
    ax.set_title('Net Primary Productivity (NPP) Comparison')
    ax.set_xticklabels(chart_data['NAME'], rotation=90)
    
    st.pyplot(fig)
