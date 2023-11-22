import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Function to fetch data
@st.cache_data
def fetch_data(url, body):
    response = requests.post(url, json=body)
    return response.json()

# Function to map codes to descriptions
def map_codes(data, code_map):
    for item in data:
        for i, key in enumerate(item['key']):
            if key in code_map:
                item['key'][i] = code_map[key]
    return data

# Function to create dataframe
def create_dataframe(data):
    records = []
    for item in data:
        # Check if the value is numeric, otherwise set it to 0 or NaN
        try:
            value = float(item['values'][0])
        except ValueError:
            value = 0  # or use `float('nan')` if you prefer NaN

        # Determine if the source is renewable or non-renewable
        is_renewable = 'förnybara' in item['key'][1] and 'icke' not in item['key'][1]

        record = {
            'region': item['key'][0],
            'energy_type': item['key'][1],
            'year': item['key'][2],
            'value': value,
            'is_renewable': is_renewable
        }
        records.append(record)
    return pd.DataFrame(records)


# Function to calculate the renewable ratio
def calculate_renewable_ratio(df):
    # Sum total energy consumption by year
    total_by_year = df.groupby('year')['value'].sum().reset_index(name='total_value')

    # Sum non-renewable energy consumption by year
    non_renewable = df[df['energy_type'].str.contains("icke förnybara")].groupby('year')['value'].sum().reset_index(name='non_renewable_value')

    # Sum fjärrvärme energy consumption by year
    fjarrvarme = df[df['energy_type'] == "fjärrvärme"].groupby('year')['value'].sum().reset_index(name='fjarrvarme_value')

    # Merge total, non-renewable, and fjärrvärme data
    merged_df = total_by_year.merge(non_renewable, on='year', how='left')
    merged_df = merged_df.merge(fjarrvarme, on='year', how='left')
    merged_df.fillna(0, inplace=True)  # Fill NaN values with 0

    # Calculate the renewable ratios
    merged_df['renewable_ratio'] = (merged_df['total_value'] - merged_df['non_renewable_value']) / merged_df['total_value']
    merged_df['renewable_excl_fjarrvarme_ratio'] = (merged_df['total_value'] - merged_df['non_renewable_value'] - merged_df['fjarrvarme_value']) / merged_df['total_value']

    return merged_df[['year', 'renewable_ratio', 'renewable_excl_fjarrvarme_ratio']]



# Streamlit app
def main():
    st.title("Andel ")

    url = 'https://api.scb.se/OV0104/v1/doris/sv/ssd/START/EN/EN0203/EN0203A/SlutAnvSektor'

    body = {
  "query": [
    {
      "code": "Region",
      "selection": {
        "filter": "item",
        "values": [
          "1382"
        ]
      }
    },
    {
      "code": "Bransle",
      "selection": {
        "filter": "item",
        "values": [
          "905",
          "910",
          "915",
          "920",
          "925",
          "930",
          "14",
          "16"
        ]
      }
    }
  ],
  "response": {
    "format": "json"
  }
}

    # Create a mapping from codes to descriptions in Swedish
    code_to_description = {
        "911": "slutanv. jordbruk, skogsbruk, fiske",
        "921": "slutanv. industri, byggverksamhet",
        "931": "slutanv. offentlig verksamhet",
        "941": "slutanv. transporter",
        "951": "slutanv. övriga tjänster",
        "98": "slutanv. småhus",
        "97": "slutanv. flerbostadshus",
        "964": "slutanv. fritidshus",
        "905": "flytande (icke förnybara)",
        "910": "fast (icke förnybara)",
        "915": "gas (icke förnybara)",
        "920": "flytande (förnybara)",
        "925": "fast (förnybara)",
        "930": "gas (förnybara)",
        "14": "fjärrvärme",
        "16": "el"
    }

    # Fetch and map data
    raw_data = fetch_data(url, body)
    mapped_data = map_codes(raw_data['data'], code_to_description)

    df = create_dataframe(mapped_data)
    renewable_ratio_df = calculate_renewable_ratio(df)

    # Merge the renewable ratio into the main DataFrame
    merged_df = df.merge(renewable_ratio_df, on='year', how='left')

    # Plotting
    fig = px.line(renewable_ratio_df, x='year', y='renewable_ratio', title='Renewable Energy Ratio Over Time')
    st.plotly_chart(fig)

    # Display the entire DataFrame

    # Reshape the DataFrame for plotting
    reshaped_df = pd.melt(renewable_ratio_df, id_vars=['year'], value_vars=['renewable_ratio', 'renewable_excl_fjarrvarme_ratio'], var_name='ratio_type', value_name='value')

    # Plotting
    fig2 = px.bar(reshaped_df, x='year', y='value', color='ratio_type', barmode='group', title='Renewable Energy Ratios Over Time')
    st.plotly_chart(fig2)

    st.write(merged_df)

if __name__ == "__main__":
    main()
