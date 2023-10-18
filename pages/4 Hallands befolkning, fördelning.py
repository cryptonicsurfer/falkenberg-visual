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

regsos = client.query('SELECT DISTINCT regsonamn, lannamn, kommunnamn, regso FROM `falkenbergcloud.scb_befolkning.dim_regso_deso`').to_dataframe()
st.header("Här bor man i Halland")

# Fetch data from BigQuery into a pandas DataFrame
query = f'''
  SELECT
    ar,
    regso, 
    sum(folkmangd) as folkmangd,
    sum(case when alder in ('75-79','80-') then folkmangd else 0 end) as folkmangd_over_75,
    sum(case when alder in ('-4','5-9','10-14','15-19') then folkmangd else 0 end) as folkmangd_under_20
  FROM `falkenbergcloud.scb_befolkning.regso_folkmangd_halland` 
  GROUP BY ar, regso
  '''
query_job = client.query(query)
df = query_job.to_dataframe()

df = df.merge(regsos,on='regso', how='left')
st.write('Fördelning av befolkningen i Halland per kommun och regionalt område')

latest_year = df['ar'].max()
df_latest_year = df[df['ar']==latest_year]

fig=px.sunburst(df_latest_year,
            path=['lannamn', 'kommunnamn', 'regsonamn'],
            values='folkmangd',
            color='folkmangd',
            color_continuous_scale='tealrose',
            height=700,
            width=900)
st.write(fig)