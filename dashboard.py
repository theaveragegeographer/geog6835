import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title('A Simple Dashboard')
st.write('This dashboard displays an NPP bar chart for all the counties from the selected state.')

@st.cache_data
def load_data():

    df = pd.read_csv("/Users/aishwaryachandrasekaran/Library/CloudStorage/OneDrive-USU/USU/Fall_25/GEOG6835/Week10/us_counties_npp_change_2002_2022.csv")
    df = df[['NAME', 'STATEFP', '2002', '2022']]
    print(df.head())

    return df

df = load_data()

state = df.STATEFP.unique()
state = st.selectbox('Select a State', state)
filtered = df[df['STATEFP'] == state]
print(filtered)

name = filtered['NAME'].values[0]
npp_2002 = filtered['2002'].values[0]
npp_2022 = filtered['2022'].values[0]

col1, col2 = st.columns(2)

nh_color = col1.color_picker('Pick NH Color', '#0000FF')
sh_color = col2.color_picker('Pick SH Color', '#FF0000')

    
fig, ax = plt.subplots(1, 1, figsize=(10, 8))

filtered.plot(kind='bar', ax=ax, color=[nh_color, sh_color], x = 'NAME', y=['2002', '2022'], 
              xlabel = "Counties in selected State",
              ylabel='NPP in Kilo tonnes'),
ax.set_title(f'Net Primary Productivity (NPP) by State')
ax.set_xticks(range(len(filtered)))
ax.set_xticklabels(filtered['NAME'], rotation=90, ha='right')
ax.set_ylim(0, 1.2)
stats = st.pyplot(fig)

