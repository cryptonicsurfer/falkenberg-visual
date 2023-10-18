import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import json
import plotly.express as px
from plotly import graph_objects as go
import plotly.graph_objs as go

# Create a credentials object using the service account info from the secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
# Initialize BigQuery client
client = bigquery.Client(credentials=credentials)

verksamhetsomrade = client.query('SELECT * FROM `falkenbergcloud.scb_budget.dim_verksamhetsomrade_kommun`').to_dataframe()
kommun = client.query('SELECT DISTINCT kommun, kommunnamn FROM `falkenbergcloud.scb_befolkning.dim_regso_deso`').to_dataframe()
st.header("Kommunens kostnadsfördelning per räkenskapsår")

# Fetch data from BigQuery into a pandas DataFrame
query = f'''
  SELECT
    *
  FROM `falkenbergcloud.scb_budget.kommun_kostnader` 
  WHERE kommun = "1382"
  '''
query_job = client.query(query)
df = query_job.to_dataframe()

df = df.merge(verksamhetsomrade, on='verksamhetsomrade', how='left')
df = df.merge(kommun, on='kommun', how='left')
# st.write(df.head())
arList = sorted(df['ar'].unique().tolist(), reverse=True)
ar = st.selectbox('Välj år', arList)
fig = px.sunburst(
    df[df['ar'] == ar], 
    path=['ar', 'aggregerad_niva', 'verksamhetsomrade_namn'], 
    values='bruttokostnad_tkr',
    labels = {'bruttokostnad_tkr': "Bruttokostnad tkr"},
    color='aggregerad_niva',  # or another column that you'd like to base the colors on
    color_discrete_sequence=px.colors.sequential.Aggrnyl,
    hover_name=None,
    hover_data={'bruttokostnad_tkr': True,}
)

# Adjust the hovertemplate for the sunburst sectors
fig.update_traces(hovertemplate='Bruttokostnad tkr: %{customdata[0]:,.0f}')
fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))
st.write(fig)


fig2 = px.bar(
    df,
    x='aggregerad_niva',
    y='bruttokostnad_tkr',
    color='verksamhetsomrade_namn',
    labels={'bruttokostnad_tkr': "Bruttokostnad tkr"},
    color_discrete_sequence=px.colors.sequential.Blues_r,
    custom_data=['bruttokostnad_tkr', 'verksamhetsomrade_namn'],
    animation_frame='ar',  # animate by year
    category_orders={"ar": df['ar'].unique()}  # Ensure years play in order
)


summed_values = df.groupby(['aggregerad_niva', 'ar'])['bruttokostnad_tkr'].sum()
y_max = summed_values.max()
fig2.update_layout(
    barmode='stack',  # Ensure bars are stacked
    showlegend=False,  # Hide the legend
    yaxis_range=[0, y_max]
)

# Adjust the hovertemplate to display bruttokostnad and verksamhetsområde namn
fig2.update_traces(
    hovertemplate="Verksamhetsområde: %{customdata[1]}<br>Bruttokostnad: %{customdata[0]:,.0f} tkr"
)
st.write(fig2)




#-------------------------------- sankey chart data restructuring and plotting ---------------------- #

# define latest year
latest_ar = df['ar'].max()
# filter df for latest year
df_year = df[df['ar']==latest_ar]


# Defining labels including the total cost as 'All Costs'
labels = ['Totala kostnader'] + df_year['aggregerad_niva'].unique().tolist() + df_year['verksamhetsomrade_namn'].unique().tolist()

sources = []
targets = []
values = []

# Adding flows from 'All Costs' to each 'aggregerad_niva'
for niva in df_year['aggregerad_niva'].unique():
    sources.append(0)  # 0 is the index of 'All Costs'
    targets.append(labels.index(niva))
    values.append(df_year[df_year['aggregerad_niva'] == niva]['bruttokostnad_tkr'].sum())

# Adding flows from each 'aggregerad_niva' to each 'verksamhetsomrade_namn'
for index, row in df_year.iterrows():
    sources.append(labels.index(row['aggregerad_niva']))
    targets.append(labels.index(row['verksamhetsomrade_namn']))
    values.append(row['bruttokostnad_tkr'])

# Creating the Sankey diagram
fig_sankey = go.Figure(go.Sankey(
    node=dict(
        label=labels,
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values
    )
))

fig_sankey.update_layout(title_text=f"Sankey diagram för kommunens kostnader år {latest_ar}", font_size=10, height=1000)
st.plotly_chart(fig_sankey)
