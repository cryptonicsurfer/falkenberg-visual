import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
# st.write(df.head())

valt_ar = st.selectbox('Välj år', sorted(df['bokslutsar'].unique().tolist(), reverse=True))

fig = px.sunburst(
    df[df['bokslutsar']==valt_ar],
    path=['bokslutsar', 'bransch_grov', 'bransch_fin','foretag'],  # Replace these with the actual columns you want to use in the sunburst chart
    values='omsattning',
    color_discrete_sequence=px.colors.sequential.Magma,
    hover_name=None,
    hover_data={'omsattning': True}
)
fig.update_traces(hovertemplate='Omsättning tkr: %{customdata[0]:,.0f}')
fig.update_layout(margin = dict(t=0, l=0, r=0, b=0))
st.header('Omsättning tkr')
st.write(fig)


# Bar chart: Total omsättning per year (tkr)
grouped_df = df.groupby('bokslutsar')['omsattning'].sum().reset_index()
fig_bar = px.bar(grouped_df, x='bokslutsar', y='omsattning', title="Total Omsättning per År (tkr)")
st.write(fig_bar)

grouped_df['growth_rate'] = grouped_df['omsattning'].pct_change() * 100  # Calculate growth rate
# fig_line = go.Figure()
# fig_line.add_trace(go.Scatter(x=grouped_df['bokslutsar'], y=grouped_df['growth_rate'], mode='lines+markers', name='Growth Rate'))
# fig_line.update_layout(title='Tillväxt % i omsättning år för år', xaxis_title='Year', yaxis_title='Growth Rate (%)')
# st.write(fig_line)

# Filter out the rows where 'bransch_grov' is 'Okänd' and include years from 2010 onwards
filtered_df = df[(df['bransch_grov'] != 'Okänd') & (df['bokslutsar'] >= '2010')]

# Group by 'bokslutsar' and 'bransch_grov', then sum the 'omsattning'
grouped_by_sector_df = filtered_df.groupby(['bokslutsar', 'bransch_grov'])['omsattning'].sum().reset_index()

# Calculate the growth rate within each sector for each year
grouped_by_sector_df['growth_rate'] = grouped_by_sector_df.groupby('bransch_grov')['omsattning'].pct_change() + 1

# Calculate the cumulative growth rate within each sector from 2010
grouped_by_sector_df['cumulative_growth'] = grouped_by_sector_df.groupby('bransch_grov')['growth_rate'].cumprod() - 1
grouped_by_sector_df['cumulative_growth'] *= 100  # Convert to percentage

# Line graph using Plotly Express for cumulative growth
fig_cumulative_growth = px.line(
    grouped_by_sector_df,
    x='bokslutsar',
    y='cumulative_growth',
    color='bransch_grov',
    title='Omsättningstillväxt i % per bransch sedan 2010',
    labels={'cumulative_growth': 'Cumulative Growth Rate (%)'}
)

st.header('Omsättningstillväxt i % per bransch sedan 2010')
st.write(fig_cumulative_growth)



# ------------------------------ för bransch nyckeltal och grafer ----------------------------- #
st.subheader('Nyckeltal per bransch:')
bransch = st.selectbox('välj bransch:', df['bransch_grov'].unique().tolist())

bransch_df = filtered_df[filtered_df['bransch_grov']==bransch]

# Bar chart: Total omsättning per year (tkr)
grouped_bransch_df = bransch_df.groupby('bokslutsar')['omsattning'].sum().reset_index()
fig_bar_bransch = px.bar(grouped_bransch_df, x='bokslutsar', y='omsattning', title=f"Total Omsättning per År (tkr) för {bransch}")
st.write(fig_bar_bransch)

bransch_df = bransch_df[bransch_df['bokslutsar']==valt_ar]
antal_bolag_totalt = df[df['bokslutsar']==valt_ar].shape[0]
antal_bolag_bransch = bransch_df['bransch_grov'].count()
anställda = bransch_df['anstallda'].sum()
omsattning = bransch_df['omsattning'].sum()

st.subheader('Snabbfakta:')
st.write(f'Antal företag (aktiebolag) år {valt_ar} är {antal_bolag_totalt:,.0f} stycken')
st.write(f'Antal företag inom {bransch}: {antal_bolag_bransch:,.0f} stycken')
st.write(f'Antal anställda inom {bransch}: {anställda:,.0f} personer')
st.write(f'Omsättning för bolag inom {bransch}: {omsattning:,.0f} KSEK')



# ------------------------------ Top 10 Companies in Each "bransch_grov" ----------------------------- #
# Add a section to display top 10 companies for selected 'bransch_grov' by revenue and employees
st.subheader(f'Top 10 företag i vald bransch år {valt_ar}:')
# selected_bransch = st.selectbox('Välj bransch för att visa topp 10 företag:', df['bransch_grov'].unique().tolist())

# Filter out data for selected bransch and year, then sort by omsattning and get top 10
top_10_omsattning = df[(df['bransch_grov'] == bransch) & (df['bokslutsar'] == valt_ar)].nlargest(10, 'omsattning')

fig_omsattning = px.bar(
    top_10_omsattning.sort_values('omsattning', ascending=False), 
    x='foretag', 
    y='omsattning',
    text='omsattning',
    labels={'foretag': 'Företag', 'omsattning': 'Omsättning'},
    title=f"Top 10 företag i {bransch} efter omsättning"
)

fig_omsattning.update_traces(texttemplate='%{text:,.0f}', textposition='inside')  # Positioning text inside the bars

# Filter out data for selected bransch and year, then sort by omsattning and get top 10
top_10_anstallda = df[(df['bransch_grov'] == bransch) & (df['bokslutsar'] == valt_ar)].nlargest(10, 'anstallda')

fig_anstallda = px.bar(
    top_10_omsattning.sort_values('anstallda', ascending=False), 
    x='foretag', 
    y='anstallda',
    text='anstallda',
    labels={'foretag': 'Företag', 'anstallda': 'Antal anställda'},
    title=f"Top 10 företag i {bransch} efter antal anställda"
)

fig_anstallda.update_traces(texttemplate='%{text:,.0f}', textposition='inside')  # Positioning text inside the bars


# display the charts in the streamlit app: ----------- #
st.write(fig_omsattning)

st.write(fig_anstallda)

# Rename to avoid conflicts with other filtered_df
sector_filtered_df = df[~df['bransch_grov'].isin(['Okänd', 'Finans och fastighetsverksamhet'])]
# sector_filtered_df = df[df['bransch_grov'] != 'Okänd']
most_recent_year = sector_filtered_df['bokslutsar'].max()
sector_filtered_df = sector_filtered_df[~((sector_filtered_df['bokslutsar'] == most_recent_year) & (sector_filtered_df['anstallda'] == 0))]

# Group by 'bransch_grov' and 'bokslutsar', sum 'omsattning', 'totalt_kapital', and 'anstallda'
sector_yearly_summary = sector_filtered_df.groupby(['bransch_grov', 'bokslutsar']).agg({'omsattning': 'sum', 'totalt_kapital': 'sum', 'anstallda': 'sum', 'eget_kapital': 'sum'}).reset_index()

# Calculate 'omsattning_per_anstalld' and 'totalt_kapital_per_anstalld'
sector_yearly_summary['omsattning_per_anstalld'] = sector_yearly_summary['omsattning'] / sector_yearly_summary['anstallda']
sector_yearly_summary['totalt_kapital_per_anstalld'] = sector_yearly_summary['totalt_kapital'] / sector_yearly_summary['anstallda']
sector_yearly_summary['eget_kapital_per_anstalld'] =sector_yearly_summary['eget_kapital'] / sector_yearly_summary['anstallda']

# Convert 'omsattning_per_anstalld' to a list for the 'size' argument in scatter plot
size_values = sector_yearly_summary['omsattning_per_anstalld'].tolist()

# Line chart for average revenue per employee
fig_avg_rev_per_emp = px.line(
    sector_yearly_summary,
    x='bokslutsar',
    y='omsattning_per_anstalld',
    color='bransch_grov',
    title='Genomsnittlig Omsättning per Anställd per Bransch Årligen',
    labels={'omsattning_per_anstalld': 'Omsättning per Anställd', 'bokslutsar': 'År', 'bransch_grov': 'Bransch'}
)
st.write(fig_avg_rev_per_emp)

# Scatter plot for capital per employee vs revenue per employee
fig_scatter = px.scatter(
    sector_yearly_summary,
    x='totalt_kapital_per_anstalld',
    y='omsattning_per_anstalld',
    animation_frame='bokslutsar',
    color='bransch_grov',
    size=size_values,
    range_x=[0, sector_yearly_summary['totalt_kapital_per_anstalld'].max()+1000],
    range_y=[0, sector_yearly_summary['omsattning_per_anstalld'].max()+1000],

    title='Totalt Kapital per Anställd vs Omsättning per Anställd per Bransch och År',
    labels={'totalt_kapital_per_anstalld': 'Totalt Kapital per Anställd', 'omsattning_per_anstalld': 'Omsättning per Anställd'}
)
st.write(fig_scatter)

# Scatter plot for capital per employee vs revenue per employee
fig_scatter2 = px.scatter(
    sector_yearly_summary,
    x='totalt_kapital_per_anstalld',
    y='eget_kapital_per_anstalld',
    animation_frame='bokslutsar',
    color='bransch_grov',
    size=size_values,
    range_x=[0, sector_yearly_summary['totalt_kapital_per_anstalld'].max()+1000],
    range_y=[0, sector_yearly_summary['eget_kapital_per_anstalld'].max()+1000],

    title='Totalt Kapital per Anställd vs Omsättning per Anställd per Bransch och År',
    labels={'totalt_kapital_per_anstalld': 'Totalt Kapital per Anställd', 'omsattning_per_anstalld': 'Omsättning per Anställd', 'eget_kapital_per_anstalld': 'Egetkapital per anställd'}
)
st.write(fig_scatter2)