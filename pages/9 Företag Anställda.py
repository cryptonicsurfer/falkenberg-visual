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

# First chart: Sunburst chart
fig_anstallda = px.sunburst(
    df[df['bokslutsar']==valt_ar],
    path=['bokslutsar', 'bransch_grov', 'bransch_fin','foretag'],
    values='anstallda',
    title='Antal Anställda',
    color_discrete_sequence=px.colors.sequential.Agsunset,
    hover_name=None,
    hover_data={'anstallda': True}
)
fig_anstallda.update_traces(hovertemplate='Antal Anställda: %{customdata[0]:,.0f}')
fig_anstallda.update_layout(margin = dict(t=0, l=0, r=0, b=0))

st.header('Antal anställda')
st.plotly_chart(fig_anstallda)

# Second chart: Column chart for top 10 companies by number of employees
top_10_companies = df[df['bokslutsar']==valt_ar].nlargest(10, 'anstallda')
top_10_companies['company_with_industry'] = top_10_companies['foretag'] + ' (' + top_10_companies['bransch_grov'] + ')'

fig_top_10 = px.bar(
    top_10_companies,
    x='company_with_industry',
    y='anstallda',
    title=f'Top 10 Företag efter Antal Anställda ({valt_ar})',
    labels={'company_with_industry': 'Företag (Bransch)', 'anstallda': 'Antal Anställda'},
    color='anstallda',
    color_continuous_scale=px.colors.sequential.Viridis,
    text='anstallda'  # Add this line to show the values on the bars
)

fig_top_10.update_traces(texttemplate='%{text}', textposition='inside')  # Position the text outside the bars

fig_top_10.update_layout(
    xaxis_tickangle=-45,
    xaxis_title=None,
    yaxis_title='Antal Anställda',
    height=600,
    uniformtext_minsize=8,  # Minimum text size
    uniformtext_mode='hide'  # Hide labels if they don't fit
)

st.header('Top 10 Företag efter Antal Anställda')
st.plotly_chart(fig_top_10)