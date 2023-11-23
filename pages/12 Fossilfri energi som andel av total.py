import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import base64

# Function to fetch data
@st.cache_data
def fetch_data(url, body):
    response = requests.post(url, json=body)
    return response.json()

# Function to map codes to descriptions
def map_codes(data, code_map, renewable_sources):
    for item in data:
        for i, key in enumerate(item['key']):
            if key in code_map:
                item['key'][i] = code_map[key]
        # Check if the source is classified as renewable
        item['is_renewable'] = item['key'][1] in renewable_sources
    return data

renewable_sources = ['flytande (förnybara)', 'fast (förnybara)', 'gas (förnybara)', 'fjärrvärme', 'el']


# Function to create dataframe
def create_dataframe(data):
    records = []
    for item in data:
        # Check if the value is numeric, otherwise set it to 0 or NaN
        try:
            value = float(item['values'][0])
        except ValueError:
            value = 0  # or use `float('nan')` if you prefer NaN

        record = {
            'region': item['key'][0],
            'energy_type': item['key'][1],
            'year': item['key'][2],
            'value': value,
            'is_renewable': item['is_renewable']  # Use the is_renewable flag from map_codes
        }
        records.append(record)
    return pd.DataFrame(records)

# Function to calculate the renewable ratio
def calculate_renewable_ratio(df):
    # Calculate the total value, non-renewable value, and fjärrvärme value for each year
    yearly_data = df.groupby('year').agg({'value': 'sum', 'is_renewable': lambda x: (x == True).sum()})
    non_renewable_data = df[~df['is_renewable']].groupby('year')['value'].sum()
    fjarrvarme_data = df[df['energy_type'] == "fjärrvärme"].groupby('year')['value'].sum()

    # Calculate the renewable ratios and convert them to percentages
    yearly_data['renewable_ratio'] = (1 - non_renewable_data / yearly_data['value']) * 100
    yearly_data['renewable_excl_fjarrvarme_ratio'] = (1 - (non_renewable_data + fjarrvarme_data) / yearly_data['value']) * 100

    return yearly_data.reset_index()[['year', 'renewable_ratio', 'renewable_excl_fjarrvarme_ratio']]


# Function to generate download link for a DataFrame
def generate_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some browsers need base64 encoding
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Streamlit app
def main():
    st.title("Andel fossilfri energi som ratio av total energikonsumtion")

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

        # Function to generate download link for a DataFrame
    def generate_download_link(df, filename, text):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some browsers need base64 encoding
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
        return href
    
    # Fetch and map data
    raw_data = fetch_data(url, body)
    mapped_data = map_codes(raw_data['data'], code_to_description, renewable_sources)

    df = create_dataframe(mapped_data)
    renewable_ratio_df = calculate_renewable_ratio(df)


    # Merge the renewable ratio into the main DataFrame
    merged_df = df.merge(renewable_ratio_df, on='year', how='left')

    # Plotting
    fig = px.line(renewable_ratio_df, x='year', y='renewable_ratio', title='Andel fossilfri energi över tid', line_shape='hv',
                labels={'renewable_ratio': 'Andel Fossilfri Energi (%)', 'year': 'År'})
    fig.update_layout(xaxis_title='År', yaxis_title='Andel Fossilfri Energi (%)')
    st.plotly_chart(fig)
    st.caption('Beräknat som summan av fossilfria energikällor dividerat med den totala energikonsumtionen')
    st.markdown(generate_download_link(renewable_ratio_df, "renewable_ratio_data.csv", 'Ladda ner data'), unsafe_allow_html=True)


    # Display the entire DataFrame

    # Reshape the DataFrame for plotting
    reshaped_df = pd.melt(renewable_ratio_df, id_vars=['year'], value_vars=['renewable_ratio', 'renewable_excl_fjarrvarme_ratio'], var_name='ratio_type', value_name='value')

    # Custom labels for the bar chart
    custom_labels = {'renewable_ratio': 'Fossilfri Energi', 'renewable_excl_fjarrvarme_ratio': 'Fossilfri Energi Exkl. Fjärrvärme', 'value': 'Andel (%)', 'year': 'År'}

    # Plotting
    fig2 = px.bar(reshaped_df, x='year', 
                  y='value', 
                  color='ratio_type', 
                  barmode='group', 
                  title='Andel fossilfri energi, och exklusive fjärrvärme',
                  labels=custom_labels)
    
    fig2.update_layout(xaxis_title='År', yaxis_title='Andel (%)', legend_title='Energityp', yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig2)
    st.markdown(generate_download_link(reshaped_df, "reshaped_data.csv", 'Ladda ner data som'), unsafe_allow_html=True)


    
    if st.button('Klicka är för att se källdatan'):
        st.write(merged_df)

if __name__ == "__main__":
    main()
