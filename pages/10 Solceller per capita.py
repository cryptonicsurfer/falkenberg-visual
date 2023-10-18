import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px


# Replace with your actual URL
url = "http://pxexternal.energimyndigheten.se/api/v1/sv/Nätanslutna solcellsanläggningar/EN0123_2.px"

# Define the header for the POST request
headers = {
    'Content-Type': 'application/json',
}

# Define the body for the POST request
payload = {
    "query": [
        {
            "code": "Område",
            "selection": {
                "filter": "item",
                "values": [
                    "0",
                    "11",
                    "151",
                    "153",
                    "154"
                ]
            }
        }
    ],
    "response": {
        "format": "json"
    }
}

# Send the POST request
response = requests.post(url, headers=headers, json=payload)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Load the JSON data from the response
    response_data = response.json()
    
    # Print or further process the JSON data
    print(json.dumps(response_data, indent=4))
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")


# helper mapping tables for json response
omrade_mapping = {
    '0' : 'sverige',
    '11' : 'halland',
    '151' : 'halmstad',
    '153' : 'falkenberg',
    '154' : 'varberg'
}

energy_measure_mapping = {
    '0' : 'Installerad effekt per capita (Watt per person)',
    '1' : 'Installerad effekt per landareal (Watt per kvadrat kilometer)'
}

# Define the base year
BASE_YEAR = 2016

# Extract data_entries from the response_data
data_entries = response_data.get('data', [])

# Creating a list to store the rows
rows = []

# Populate the rows list based on the response data
for entry in data_entries:
    year = BASE_YEAR + int(entry['key'][0])
    omrade = omrade_mapping.get(entry['key'][1], "Unknown Område")
    energy_measure = energy_measure_mapping.get(entry['key'][3], "Unknown Measure")
    value = float(entry['values'][0]) if entry['values'] else "No Value"

    # Append the data into the rows list
    rows.append({
        'Year': year,
        'Område': omrade,
        'Energy Measure': energy_measure,
        'Value': value
    })

# Convert the rows list to a DataFrame
df = pd.DataFrame(rows)

# Convert 'Year' and 'Value' to int    
# Forward filling the missing values in the 'Year' column
df['Year'] = df['Year'].fillna(method='ffill')
df['Year'] = df['Year'].astype(int)
df['Value'] = df['Value'].astype(int)



df_per_capita = df[df['Energy Measure']=='Installerad effekt per capita (Watt per person)']

df_per_capita = df_per_capita.sort_values(by=['Område', 'Year'])
# Getting the unique energy measure as a string
energy_measure_title = str(df_per_capita['Energy Measure'].unique()[0])


fig = px.line(df_per_capita, x = 'Year', y = 'Value', color='Område', labels={'Value': 'Watt per invånare'}, title=energy_measure_title)

st.plotly_chart(fig)

df_land_m2 = df[df['Energy Measure']=='Installerad effekt per landareal (Watt per kvadrat kilometer)']
df_land_m2 = df_land_m2.sort_values(by=['Område', 'Year'])
# Getting the unique energy measure as a string
energy_measure_title = str(df_land_m2['Energy Measure'].unique()[0])


fig2 = px.line(df_land_m2, x='Year', y='Value', color='Område', labels={'Value':'Watt per kvadratkilometer'}, title=energy_measure_title)

st.plotly_chart(fig2)

latest_year = df['Year'].max()

df_land_m2_filtered = df_land_m2[df_land_m2['Year']==latest_year]
df_per_capita_filtered = df_per_capita[df_per_capita['Year']==latest_year]

df_land_m2_filtered = df_land_m2_filtered.sort_values(by='Område').reset_index(drop=True)
df_per_capita_filtered = df_per_capita_filtered.sort_values(by='Område').reset_index(drop=True)

# Merging two dataframes on Område and Year
merged_df = pd.merge(df_land_m2_filtered, df_per_capita_filtered, on=['Område', 'Year'], suffixes=('_land_m2', '_per_capita'))


fig3 = px.scatter(merged_df,
                  x='Value_land_m2',
                  y='Value_per_capita',
                #   labels={'x': 'Land M2 Value', 'y': 'Per Capita Value'},
                  size='Value_per_capita',
                  color='Område',
                  text='Område',
                  title='Scatter Plott',
                  labels={
                      'Value_land_m2': 'Watt per kvadratkilometer',
                      'Value_per_capita': 'Watt per invånare'
                  })

st.plotly_chart(fig3)

link = 'https://pxexternal.energimyndigheten.se/pxweb/sv/Nätanslutna%20solcellsanläggningar/-/EN0123_2.px/'
st.write(f'källa: [energimyndigheten]({link}) statistikdatabas')
