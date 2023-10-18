import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import json
import plotly.express as px


# Create a credentials object using the service account info from the secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
# Initialize BigQuery client
client = bigquery.Client(credentials=credentials)


regsos = client.query('SELECT DISTINCT regsonamn, regso FROM `falkenbergcloud.scb_befolkning.dim_regso_deso`').to_dataframe()


# Fetch data from BigQuery into a pandas DataFrame
query = f'''
  SELECT
    ar,
    regso, 
    sum(folkmangd) as folkmangd,
    sum(case when alder in ('75-79','80-') then folkmangd else 0 end) as folkmangd_over_75,
    sum(case when alder in ('-4','5-9','10-14','15-19') then folkmangd else 0 end) as folkmangd_under_20
  FROM `falkenbergcloud.scb_befolkning.regso_folkmangd` 
  GROUP BY ar, regso
  '''
query_job = client.query(query)
df = query_job.to_dataframe()

df = df.merge(regsos, on='regso', how='left')
# Calculate the fraction for folkmangd_under_20 as a percentage
df['folkmangd_under_20%'] = (df['folkmangd_under_20'] / df['folkmangd']) * 100
# Calculate the fraction for folkmangd_over_75 as a percentage
df['folkmangd_over_75%'] = (df['folkmangd_over_75'] / df['folkmangd']) * 100
latest_ar = df['ar'].max()
df_latest_ar = df[df['ar']==latest_ar]


@st.cache_data
def load_geojson(path):
    with open(path, 'r') as f:
        return json.load(f)

# Call the cached function
geojson = load_geojson('pages/geodata/regso_falkenberg.geojson')

st.header("Geografisk- samt åldersfördelning i Falkenberg")

# Create a choropleth map using Mapbox
fig = px.choropleth_mapbox(df_latest_ar, geojson=geojson, locations='regso', color='folkmangd',
                           color_continuous_scale="temps",
                           labels={'folkmangd':'Folkmängd'},
                           center={"lat": 57.000, "lon": 12.4912},  # Center on Falkenberg
                           zoom=8,  # Adjust the zoom level as needed
                           hover_name='regsonamn',
                           custom_data=['folkmangd', 'folkmangd_over_75%', 'folkmangd_under_20%'],
                           mapbox_style="carto-positron"  # You can use other mapbox styles like "open-street-map", "light", "dark", etc.
                          )

fig.update_traces(marker_opacity=0.2)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.update_traces(
    hovertemplate="<br>".join([
        "Regso Namn: %{hovertext}",
        "Folkmängd: %{customdata[0]:,.0f}",
        "Folkmängd över 75 år: %{customdata[1]:.2f}%",
        "Folkmängd under 20 år: %{customdata[2]:.2f}%"
    ])
)
st.write(fig)

st.write('Regionalt statistikområde Falkenberg Södra (Herting, Hjortsberg, Kristineslätt, Slätten och Näset) är Falkenbergs folkrikaste område. ')

# Create a bubble plot using plotly
bubble_fig = px.scatter(df,
                        y='folkmangd_over_75%',
                        x='folkmangd_under_20%',
                        size=df['folkmangd'].tolist(),
                        animation_frame='ar',
                        text=df['regsonamn'],
                        color='folkmangd',  # Color the bubbles based on folkmangd
                        color_continuous_scale="temps",  
                        hover_name='regsonamn',
                        size_max=60,  # you can adjust this for the maximum bubble size
                        custom_data=['folkmangd', 'folkmangd_over_75%', 'folkmangd_under_20%'],
                        # title="Befolkning per område",
                        height=700,
                        labels={'folkmangd_over_75%':'Andel över 75 år, i %', 'folkmangd_under_20%': 'Andel under 20 år, i %', 'folkmangd': 'Folkmängd', 'ar': 'År'})

bubble_fig.update_traces(
    hovertemplate="<br>".join([
        "Regso Namn: %{hovertext}",
        "Folkmängd: %{marker.size:,.0f}",
        "Folkmängd över 75 år: %{y:.2f}%",
        "Folkmängd under 20 år: %{x:.2f}%"
    ])
)
bubble_fig.update_traces(marker_opacity=0.5)
bubble_fig.update_traces(marker=dict(line=dict(width=1, color='Coral')))
bubble_fig.update_traces(textposition='top center')
bubble_fig.update_layout(
    xaxis=dict(
        title_font=dict(size=18),  # Adjust size as needed for x-axis title
        tickfont=dict(size=16)  # Adjust size as needed for x-axis tick labels
    ),
    yaxis=dict(
        title_font=dict(size=18),  # Adjust size as needed for y-axis title
        tickfont=dict(size=16)  # Adjust size as needed for y-axis tick labels
    )
)

st.write('---')
st.subheader('Folkmängd per område över tid (med animation)')
st.write(bubble_fig)
st.write('Falkenberg Centrum, har högst andel äldre och lägst andel yngre. Skrea har lägst andel äldre, samt den högsta andelen yngre. Från 2016 har andelen över 75 år ökat i flertalet områden, särskilt i Glommen syns denna utveckling.')