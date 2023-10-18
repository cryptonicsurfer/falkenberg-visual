import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px

st.set_page_config(layout="centered")

# Create a credentials object using the service account info from the secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials)


# Fetch data from BigQuery into a pandas DataFrame
query = '''
SELECT
    alder, 
    'Falkenberg' as kommun,
    ar,
    sum(folkmangd) as folkmangd 
FROM `falkenbergcloud.scb_befolkning.folkmangd`
WHERE kommun = '1382'
GROUP BY
alder, kommun, ar
'''
df = client.query(query).to_dataframe()

# Process data
df['age_group'] = (df['alder'].str.replace("+", "").astype(int) // 10) * 10
df = df.groupby(['age_group', 'ar'])['folkmangd'].sum().reset_index()
df['age_group_label'] = df['age_group'].apply(lambda x: f"{x}-{x+9} år").str.replace("-109", "+")
df.rename(columns={
    'age_group': "Åldersgrupp",
    'ar': 'År',
    'folkmangd': 'Befolkningsmängd',
    'age_group_label': 'Åldersgrupper'
}, inplace=True)




df_cagr = df.copy()

def compute_cagr(end_value, start_value, years_diff):
    """Compute the CAGR given starting and ending values and number of years."""
    return ((end_value / start_value) ** (1/years_diff) - 1) #* 100

df_cagr['CAGR % to current year'] = 0.0

# Convert the year values to integers while fetching the maximum year
end_year = int(df_cagr['År'].max())

# Loop over each unique year in our dataset.
# Convert each year to an integer before using it.
for year in df_cagr['År'].unique():
    year = int(year)
    mask = df_cagr['År'] == str(year)
    
    end_values = df_cagr[df_cagr['År'] == str(end_year)].set_index('Åldersgrupp')['Befolkningsmängd']
    
    for group in df_cagr['Åldersgrupp'].unique():
        start_value = df_cagr.loc[mask & (df_cagr['Åldersgrupp'] == group), 'Befolkningsmängd'].values[0]
        
        if group in end_values:
            end_value = end_values[group]
            years_diff = end_year - year
            
            # Skip the computation if years_diff is zero
            if years_diff == 0:
                continue
            
            cagr_value = compute_cagr(end_value, start_value, years_diff)
            
            df_cagr.loc[mask & (df_cagr['Åldersgrupp'] == group), 'CAGR % to current year'] = cagr_value




# Fetch data from BigQuery into a pandas DataFrame

query_prog = '''
SELECT
    alder, 
    'Falkenberg' as kommun,
    ar,
    sum(folkmangd) as folkmangd 
FROM `falkenbergcloud.scb_befolkning.folkmangd_prognos`
WHERE kommun = '1382'
GROUP BY
alder, kommun, ar
'''
df_prog = client.query(query_prog).to_dataframe()

# Process data
df_prog['age_group'] = (df_prog['alder'].str.replace("+", "").astype(int) // 10) * 10
df_prog = df_prog.groupby(['age_group', 'ar'])['folkmangd'].sum().round().reset_index()
df_prog['age_group_label'] = df_prog['age_group'].apply(lambda x: f"{x}-{x+9} år").str.replace("-109", "+")
df_prog.rename(columns={
    'age_group': "Åldersgrupp",
    'ar': 'År',
    'folkmangd': 'Befolkningsmängd',
    'age_group_label': 'Åldersgrupper'
}, inplace=True)



# Create plots
min_value, max_value = df['Befolkningsmängd'].min(), df['Befolkningsmängd'].max()
fig = px.bar(df,
             x='Befolkningsmängd',
             y='Åldersgrupper',
             animation_frame='År',
             color='Åldersgrupp',
             labels={'Befolkningsmängd': 'Befolkningsmängd', 'Åldersgrupp': 'Åldersgrupp'},
             orientation='h',
             color_continuous_scale='agsunset',
             text=df['Befolkningsmängd'],
             height=700,
             width=700)
fig.update_traces(textposition='outside')
fig.update_layout(xaxis=dict(range=[min_value, max_value]))
fig.update_layout(coloraxis_showscale=False)

df_pop = df.groupby(['År'])['Befolkningsmängd'].sum().reset_index()
fig2 = px.bar(df_pop,
              x='År',
              y='Befolkningsmängd',
              labels={'Befolkningsmängd': 'Befolkningsmängd', 'År': 'År'},
              color='Befolkningsmängd',
              color_continuous_scale='agsunset',
              height=640,)

fig2.update_layout(coloraxis_showscale=False, yaxis_title=None)


# prog charts
min_value, max_value = df_prog['Befolkningsmängd'].min(), df_prog['Befolkningsmängd'].max()
fig_prog = px.bar(df_prog,
             x='Befolkningsmängd',
             y='Åldersgrupper',
             animation_frame='År',
             color='Åldersgrupp',
             labels={'Befolkningsmängd': 'Befolkningsmängd', 'Åldersgrupp': 'Åldersgrupp'},
             orientation='h',
             color_continuous_scale='agsunset',
             text=df_prog['Befolkningsmängd'],
             height=700,
             width=700)
fig_prog.update_traces(textposition='outside')
fig_prog.update_layout(xaxis=dict(range=[min_value, max_value]))
fig_prog.update_layout(coloraxis_showscale=False)


df_prog_pop = df_prog.groupby(['År'])['Befolkningsmängd'].sum().reset_index()
fig2_prog = px.bar(df_prog_pop,
              x='År',
              y='Befolkningsmängd',
              labels={'Befolkningsmängd': 'Befolkningsmängd', 'År': 'År'},
              color='Befolkningsmängd',
              color_continuous_scale='agsunset',
              height=640)
fig2_prog.update_layout(coloraxis_showscale=False, yaxis_title=None)

config = {'displaylogo': False, 'use_container_width': True}





# st.subheader('Befolkning i grafer')
st.subheader('Befolkningsutveckling sedan 1968')
st.plotly_chart(fig2, config=config)


st.subheader('Folkmängd 10-års åldersgrupper sedan 1968, animerad')
st.plotly_chart(fig, config=config)


# color=st.selectbox('välj färg',  ['ggplot2', 'seaborn', 'simple_white', 'plotly',
#          'plotly_white', 'plotly_dark', 'presentation', 'xgridoff',
#          'ygridoff', 'gridon', 'none'])

# fig_cagr = px.line(df_cagr, x='År', 
#                    y='CAGR % to current year', 
#                    line_group='Åldersgrupper', 
#                    color='Åldersgrupper',
#                    template=color,)
# # Update y-axis format to percentage
# fig_cagr.update_yaxes(tickformat="%", range=[-0.03, 0.06]) #tickformat="%", 
# st.plotly_chart(fig_cagr, config=config)

st.subheader('Befolkningsprognos till 2070')
st.plotly_chart(fig2_prog, config=config)


st.subheader('Prognos folkmängd 10-års åldersgrupper till 2070, animerad')
st.plotly_chart(fig_prog, config=config)

