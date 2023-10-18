import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px

# Create a credentials object using the service account info from the secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
# Initialize BigQuery client
client = bigquery.Client(credentials=credentials)

@st.cache_data
def get_company_data():
  query = '''
    SELECT * FROM `falkenbergcloud.dnb_data.dnb_ab_falkenberg`
  '''
  df = client.query(query).to_dataframe()
  return df


st.title("Företagen i Falkenberg (AB)")
df = get_company_data()


valt_ar = st.selectbox('Välj år', sorted(df['bokslutsar'].unique().tolist(), reverse=True))

fig_anstallda = px.sunburst(
    df[df['bokslutsar']==valt_ar],
    path=['bokslutsar', 'bransch_grov', 'bransch_fin','foretag'],  # Replace these with the actual columns you want to use in the sunburst chart
    values='anstallda',
    title='Antal Anställda',
    color_discrete_sequence=px.colors.sequential.Agsunset,
    hover_name=None,
    hover_data={'anstallda': True}
)
fig_anstallda.update_traces(hovertemplate='Antal Anställda: %{customdata[0]:,.0f}')
fig_anstallda.update_layout(margin = dict(t=0, l=0, r=0, b=0))
st.header('Antal anställda')
st.write(fig_anstallda)