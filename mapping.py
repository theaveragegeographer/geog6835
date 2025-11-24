import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import leafmap.foliumap as leafmap
import requests
from io import BytesIO
import zipfile
import mapclassify

st.set_page_config(page_title='NPP Dashboard', layout='wide')

st.title('Net Primary Productivity Dashboard')
st.write('This dashboard can be used for visualizing Net Primary Productivity (NPP) changes over time. ' \
'Visualizations are produced at the county scale. Please select a state using the STATEFP code ' \
'to display NPP change from 2002 to 2022. A quantitative bar chart shows the increase or descrease in NPP between 2002 and 2022.')

st.info("Note: This app uses TIGER/LINE census data to visualize the maps")

st.sidebar.title('About')
st.sidebar.info('Explore the Net Primary Productivity Statistics')

# Pick colors for the bars
col1, col2 = st.sidebar.columns(2)

nh_color = col1.color_picker('Pick NH Color', "#86BFE0")
sh_color = col2.color_picker('Pick SH Color', "#C66762")

# Cache the geodata loading
@st.cache_data
def load_tiger_counties():
    """Load US Census TIGER/Line Shapefile for counties"""
    # TIGER/Line Shapefiles URL for counties (2023)
    tiger_url = "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip"
    
    with st.spinner("Loading US Census TIGER county shapefiles..."):
        # Download and extract
        response = requests.get(tiger_url)
        z = zipfile.ZipFile(BytesIO(response.content))
        z.extractall("/tmp/tiger_counties")
        
        # Read shapefile
        gdf = gpd.read_file("/tmp/tiger_counties/tl_2023_us_county.shp")
        gdf['GEOID'] = gdf['GEOID'].astype(str).str.zfill(5)
        gdf = gdf.to_crs(epsg=4326)
        print(gdf.head())
    return gdf



# gpkg_file = 'karnataka.gpkg'
# csv_file = 'highway_lengths_by_district.csv'


url = "/Users/aishwaryachandrasekaran/Library/CloudStorage/OneDrive-USU/USU/Fall_25/GEOG6835/Week10/us_counties_npp_change_2002_2022.csv"
@st.cache_data
def read_csv(url):
    df = pd.read_csv(url)
    df = df[['NAME', 'GEOID', 'STATEFP', '2002', '2022', 'NPP_Change']]
    df['STATEFP'] = df['STATEFP'].astype(str).str.zfill(2)
    df['GEOID'] = df['GEOID'].astype(str).str.zfill(5)
    return df


TIGER = load_tiger_counties()
lengths_df = read_csv(url)

states = lengths_df.STATEFP.unique()
selected_state = st.sidebar.selectbox('Select a State', states)

state_lengths = lengths_df[lengths_df['STATEFP'] == selected_state]

#Create description statistics
st.sidebar.dataframe(state_lengths.describe())

## Create the map

st.write("## Visualize NPP Change from 2002 to 2022")

selected_gdf = TIGER[TIGER['STATEFP'] == selected_state]
print(selected_gdf.head())

selected_gdf = selected_gdf.merge(state_lengths, on='GEOID', how='left')

m = leafmap.Map(
    layers_control=True,
    draw_control=False,
    measure_control=False,
    fullscreen_control=False,
)
m.add_basemap('CartoDB.DarkMatter')

print(selected_gdf.head())

m.add_data(
    selected_gdf,
    layer_name='Selected Counties',
    column="NPP_Change", scheme="Quantiles", cmap="RdYlGn",
    zoom_to_layer=True,
    info_mode=None,
 )

m_streamlit = m.to_streamlit(1000, 600)

#Create a split map
st.write("## Visualize NPP in 2002 and 2022")
m = leafmap.Map(
    layers_control=True,
    draw_control=False,
    measure_control=False,
    fullscreen_control=False,
)
m.add_data(
    selected_gdf,
    layer_name='NPP2002',
    column="2002", scheme="Quantiles", cmap="RdYlGn",
    zoom_to_layer=True,
    info_mode=None,
 )
m.add_data(
    selected_gdf,
    layer_name='NPP2022',
    column="2022", scheme="Quantiles", cmap="RdYlGn",
    zoom_to_layer=True,
    info_mode=None,
 )

m_split_streamlit = m.to_streamlit(1000, 600)

# Create the chart
st.write("## Bar Chart of NPP from 2002 to 2022")
fig, ax = plt.subplots(1, 1,figsize=(10, 8))
state_lengths.plot(kind='bar', ax=ax, color=[nh_color, sh_color], x = 'NAME', y=['2002', '2022'], 
              xlabel = "Counties in selected State",
              ylabel='NPP in Kilo tonnes'),
ax.set_title(f'Net Primary Productivity (NPP) by State')
ax.set_xticks(range(len(state_lengths)))
ax.set_xticklabels(state_lengths['NAME'], rotation=90, ha='right')
ax.set_ylim(0, 1.5 * state_lengths[['2002', '2022']].values.max())
stats = st.pyplot(fig)

