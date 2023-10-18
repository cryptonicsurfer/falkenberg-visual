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

regsos = client.query('SELECT DISTINCT kommunnamn, lannamn, lan, regsonamn, regso FROM `falkenbergcloud.scb_befolkning.dim_regso_deso`').to_dataframe()

# Fetch data from BigQuery into a pandas DataFrame
query = f'''
  SELECT 
  *
  FROM `falkenbergcloud.scb_budget.kommunala_skulden_investeringar`
  WHERE region_T_F = 0 AND koncern_T_F = 1
  '''
query_job = client.query(query)
df = query_job.to_dataframe()



df['skuld_per_capita'], df['investeringar_per_capita'] = df['laneskuld']/df['folkmangd'], df['investeringar']/df['folkmangd']

max_ar = df['ar'].max()
df_histo = df[df['ar']==max_ar]
# df_histo = df_histo[df_histo['koncern_T_F']==1]
falkenberg = df_histo[df_histo['kommunkod']=='1382']

falkenberg_skuld_per_capita = df_histo[df_histo['kommunkod'] == '1382']['skuld_per_capita'].values[0]



fig_histo = px.histogram(df_histo, 
                         x='skuld_per_capita',
                         color='koncern_T_F',
                         nbins=30,
                         title=f'För år {max_ar}, är skulden per capita i Falkenberg {falkenberg_skuld_per_capita:.0f} kronor',
                         labels={'skuld_per_capita': 'Kommunal skuld per capita'},
                         color_discrete_sequence=['blue', 'red'],
                         ) 

fig_histo.update_layout(barmode='overlay', bargap=0.1)
fig_histo.update_traces(opacity=0.8)  # To make bars slightly transparent
fig_histo.update_layout(showlegend=False)

fig_histo.for_each_trace(lambda t: t.update(marker=dict(line=dict(color='darkslategray', width=2))))

st.subheader(f'Antal kommuner per olika nivåer av kommunal skuld per capita, för {max_ar}',)
st.plotly_chart(fig_histo)



# ---------- filter df on only "koncern == 1",  Create a new column 'label' initialized to None
filtered_df = df

filtered_df['label'] = None

# Set the label for the specific point you want to annotate. 
# For instance, if you want to label the point with kommun_region = "SomeName":
filtered_df.loc[filtered_df['kommun_region'] == "FALKENBERG", 'label'] = filtered_df['kommun_region']
filtered_df = filtered_df.sort_values(by='ar')

fig_fbg = px.scatter(filtered_df,
                 x='skuld_per_capita',
                 y='investeringar_per_capita',
                 size=filtered_df['folkmangd'].tolist(),
                 color='kommun_region',
                 color_continuous_scale='Agsunset',
                 animation_frame='ar',
                 range_x=[0, filtered_df['skuld_per_capita'].max()+10000],
                 range_y=[0, filtered_df['investeringar_per_capita'].max()-30000],
                 text='label',  # Use the 'label' column for text
                 size_max=55)
fig_fbg.update_traces(marker=dict(opacity=0.8))

st.subheader('Kommuner efter skuld per invånare (x-axel) samt investeringar per invånare (y-axel), animerat per år')
st.plotly_chart(fig_fbg)


# ----- filter on halland==13, sort 'ar' for animation frame ----------- #
filtered_df = filtered_df[filtered_df['lankod']=='13']
filtered_df =filtered_df.sort_values(by='ar')



fig = px.scatter(filtered_df,
                 x='folkmangd',
                 y='skuld_per_capita',
                 size = filtered_df['laneskuld'].tolist(), #filtered_df['folkmangd'].tolist(), #filtered_df['skuld_per_capita'].tolist(),
                 color = 'kommun_region',
                 color_continuous_scale='Agsunset',
                 animation_frame='ar',
                 range_x=[0, filtered_df['folkmangd'].max()+5000],
                 range_y=[0, filtered_df['skuld_per_capita'].max()+10000],
                 text='kommun_region',
                 size_max=55,
                 template = 'plotly_dark')


st.subheader('Kommunal låneskuld per capita inom Halland')
st.plotly_chart(fig)


# -------------- data manipulation and creation of bubble chart based on kommungrupp -----------------#
df_kommungrupp = df.groupby(['kommungrupp', 'ar'])[['skuld_per_capita', 'investeringar_per_capita']].mean().reset_index()
sorted_df_kommungrupp =df_kommungrupp.sort_values(by='ar')

max_x=sorted_df_kommungrupp['skuld_per_capita'].max()
max_y=sorted_df_kommungrupp['investeringar_per_capita'].max()

fig2 = px.scatter(sorted_df_kommungrupp,
                  x='skuld_per_capita',
                  y='investeringar_per_capita',
                  size=sorted_df_kommungrupp['skuld_per_capita'].tolist(),
                  color='kommungrupp',
                  color_continuous_scale='Agsunset',
                  animation_frame='ar',
                  template='plotly_dark')

fig2.update_layout(xaxis=dict(range=[0, max_x+5000]))
fig2.update_layout(yaxis=dict(range=[0, max_y+5000]))

st.subheader('Kommunal låneskuld samt investeringar per capita efter typ av kommun efter SKRs kommunindelning ')
st.write('Falkenberg är i SKRs kommungrupp "mindre stad/tätort"')
st.plotly_chart(fig2)

