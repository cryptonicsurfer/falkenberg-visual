import streamlit as st
import pandas as pd
import plotly.express as px
import json
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objs as go

# Create a credentials object using the service account info from the secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials)


# -------------------------------------------- creating SQL query functions ----------------- #

@st.cache_data
def get_regsos():
    query = 'SELECT DISTINCT kommunnamn, lannamn, lan, regsonamn, regso FROM `falkenbergcloud.scb_befolkning.dim_regso_deso`'
    return client.query(query).to_dataframe()


@st.cache_data
def get_inkomst_table():
    query = f'''
      SELECT 
      *
      FROM `falkenbergcloud.scb_befolkning.regso_kon_inkomst_halland`
      '''
    return client.query(query).to_dataframe()


@st.cache_data
def get_transfereringar_table():
    query = f'''
      SELECT 
      *
      FROM `falkenbergcloud.scb_befolkning.regso_transfereringar_halland`
      '''
    return client.query(query).to_dataframe()


@st.cache_data
def get_regso_folkmangd_table():
    query = f'''
      SELECT ar, regso, SUM(folkmangd) as folkmangd
      FROM `falkenbergcloud.scb_befolkning.regso_folkmangd_halland`
      GROUP BY ar, regso
      '''
    return client.query(query).to_dataframe()



# Get regsos data
regsos = get_regsos()

# Get data from a regso_kon_inkomst_halland table
df = get_inkomst_table()

# Get data from a regso_transfereringar_halland table
df_transf = get_transfereringar_table()

# Get data from a regso_folkmangd_halland table
df_folkmangd = get_regso_folkmangd_table()


# ---------------------------------------- data manipulation -------------------------------------------- #
# merge df and regsos for regsonamn
df = df.merge(regsos, on='regso', how='inner')

# create df_kon_fbg for barchart, only Falkenberg, both male and female
df_kon_fbg = df[df['kommunnamn']=='Falkenberg']

# df groupby on 'ar regso regsonamn and kommunnamn and calculate average salary regardless of "kön"
df = df.groupby(['ar', 'regso', 'regsonamn', 'kommunnamn']).agg({'nettoinkomst_tkr': 'mean'}).reset_index()

# create df_merged from df and df_transf that holds transfereringar on regso and ar level
df_merged = df.merge(df_transf, left_on=['regso', 'ar'], right_on=['regso', 'ar'], how='inner')

# create df_filtered from df_merged for only Falkenberg kommun values
df_filtered = df_merged[df_merged['kommunnamn']=='Falkenberg']

# merge df_filtered with df_folkmangd to get column with population
df_filtered = df_filtered.merge(df_folkmangd, on=['regso', 'ar'], how='inner')


# ---------------------------------------- chart creation ------------------------------------------------- #
# Color picker for background and gridlines
# background_color = st.color_picker('Pick a background color', '#FFFFFF') # Default white
# gridline_color = st.color_picker('Pick a gridline color', '#DDDDDD')     # Default light gray


# create bubble chart using px scatter, animation based on 'ar'
fig = px.scatter(df_filtered,
                 x='nettoinkomst_tkr',
                 y='andel_sjuk_och_stod_av_nettoinkomst',
                 color='regsonamn',
                 size=df_filtered['folkmangd'].tolist(),
                 animation_frame = 'ar',
                 range_y=[0, df_filtered['andel_sjuk_och_stod_av_nettoinkomst'].max()+2],
                 range_x=[150, df['nettoinkomst_tkr'].max()-100],
                 color_continuous_scale='Agsunset',
                 template='plotly_dark',
                 size_max=35,
                 text='regsonamn',
                 labels={
                     'nettoinkomst_tkr': 'Nettoinkomst per år, KSEK',
                     'andel_sjuk_och_stod_av_nettoinkomst': 'Andel av nettoinkomst från sjuk-, stöd- eller annan ersättning'
                 })

# Customize the background colors and gridlines
# fig.update_layout(
#     plot_bgcolor=background_color,
#     paper_bgcolor=background_color,
#     xaxis=dict(showgrid=True, gridcolor=gridline_color),
#     yaxis=dict(showgrid=True, gridcolor=gridline_color)
# )

fig.update_layout(showlegend=False)
fig.update_traces(marker={"opacity":0.7}) #equiv of fig.update_traces(marker=dict(opacity=0.7))

# fig2 creation and pre-processing of df_kon_fbg ------------ #
color_map = {'1': 'man', '2': 'kvinna'}
df_kon_fbg['kön']=df_kon_fbg['kon'].map(color_map)

final_year = df_kon_fbg['ar'].max()
order = df_kon_fbg[df_kon_fbg['ar'] == final_year].sort_values(by='nettoinkomst_tkr', ascending=True)['regsonamn'].tolist()
df_kon_fbg['sort'] = df_kon_fbg['regsonamn'].apply(lambda x: order.index(x))
df_kon_fbg = df_kon_fbg.sort_values(by=['sort', 'ar'])


fig2 = px.bar(df_kon_fbg,
              x = 'regsonamn',
              y = 'nettoinkomst_tkr',
              color = 'kön',
              animation_frame = 'ar',
              color_discrete_sequence=["magenta", "teal"],
              barmode='group',
              range_y=[100, df_kon_fbg['nettoinkomst_tkr'].max()],
              template='plotly_dark',
              labels={'regsonamn': 'Geografiskt område', 'nettoinkomst_tkr': 'Nettoinkomst, KSEK'}
              )

fig2.update_layout(
    xaxis_title_standoff = 60  # adjust this value as needed
)


fig2.update_traces(marker=dict(opacity=0.8)) 

st.header('Nettoinkomst per område samt hur stor andel av områdets totala nettoinkomst som kommer från sjuk- eller annat stöd')

st.plotly_chart(fig)

st.header('Animerad graf över nettoinkomst uppdelat per område samt kön, animerat per år')

st.plotly_chart(fig2)

### ------------------------------------- ###
