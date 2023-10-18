import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go

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
      "code": "Forbrukningskategri",
      "selection": {
        "filter": "item",
        "values": [
          "911", "921", "931", "941", "951", "98", "97", "964"
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
    },
    {
      "code": "Tid",
      "selection": {
        "filter": "item",
        "values": [
          "2021"
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


response = requests.post(url=url, json=body)

if response.status_code != 200:
    raise ValueError('Failed to retrieve data from the server. ')
json_response = response.json()

# Create a dictionary of unique items with their respective indices
unique_items = {}
counter = 0
for item in json_response["data"]:
    for idx, sub_item in enumerate(item["key"]):
        if idx == 0:  # Skip the first key
            continue
        if sub_item not in unique_items:
            unique_items[sub_item] = counter
            counter += 1

# Create more descriptive labels using the Swedish descriptions mapping
labels = [code_to_description.get(key, key) for key in unique_items.keys()]


# Create the source, target, and value lists
source = []
target = []
value = []

for item in json_response["data"]:
    for idx, sub_item in enumerate(item["key"][:-1]):
        if idx == 0:  # Skip the first key for source, target linking
            continue
        target.append(unique_items[sub_item])
        source.append(unique_items[item["key"][idx + 1]])
        value.append(int(item["values"][0]))

# Create Sankey chart
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=20,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=labels,  # Use the descriptive labels
    ),

    link=dict(
        source=source,
        target=target,
        value=value,
        # color='rgba(1, 75, 255, 0.4)',
        
    ))])

fig.update_layout(
    margin=dict(t=100, b=100, l=0, r=100),
)
fig.update_layout(width=800, height=600)



st.subheader('Sankey chart för hur olika energikällor används av slutanvändare per kategori, Falkenberg')
st.write(fig)




