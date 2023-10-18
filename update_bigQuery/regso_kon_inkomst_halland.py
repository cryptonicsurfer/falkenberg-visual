import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import requests


# Create a credentials object using the service account info from the secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
# Create BigQuery Dataset and Table
dataset_name = "scb_befolkning"
table_name = "regso_kon_inkomst_halland"

# Function to create BigQuery table
def create_bigquery_table(client, dataset_name, table_name):
    dataset_id = f"{client.project}.{dataset_name}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "EU"
    
    try:
        dataset = client.create_dataset(dataset)
        st.write(f"Dataset created: {dataset_id}")
    except Exception as e:
        st.write(f"Dataset exists: {dataset_id}")

    schema = [
        bigquery.SchemaField("regso", "STRING"),
        bigquery.SchemaField("kon", "STRING"),
        bigquery.SchemaField("ar", "STRING"),
        bigquery.SchemaField("nettoinkomst_tkr", "FLOAT")

    ]

    table_id = f"{client.project}.{dataset_name}.{table_name}"
    
    try:
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        st.write(f"Table created: {table_id}")
    except Exception as e:
        st.write(f"Table exists: {table_id}. Error: {e}")

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials)

# Streamlit App
st.title("Streamlit + BigQuery Example")


if st.button('Create BQ table'):
    create_bigquery_table(client, dataset_name, table_name)

# Button to Fetch and Insert Data
if st.button("Fetch and Insert Data"):
    try:
        # Fetch data from web API
        try:
            payload = {
  "query": [
    {
      "code": "Region",
      "selection": {
        "filter": "vs:RegSoHE",
        "values": [
          "1315R001","1315R002","1315R003","1315R004","1315R005","1315R006","1315R007","1380R001","1380R002","1380R003","1380R004","1380R005","1380R006","1380R007","1380R008","1380R009","1380R010","1380R011","1380R012","1380R013","1380R014","1380R015","1380R016","1380R017","1380R018","1380R019","1380R020","1380R021","1380R022","1380R023","1380R024","1380R025","1380R026","1380R027","1380R028","1381R001","1381R002","1381R003","1381R004","1381R005","1381R006","1381R007","1381R008","1381R009","1381R010","1381R011","1382R001","1382R002","1382R003","1382R004","1382R005","1382R006","1382R007","1382R008","1382R009","1382R010","1382R011","1382R012","1382R013","1382R014","1383R001","1383R002","1383R003","1383R004","1383R005","1383R006","1383R007","1383R008","1383R009","1383R010","1383R011","1383R012","1383R013","1383R014","1383R015","1383R016","1383R017","1384R001","1384R002","1384R003","1384R004","1384R005","1384R006","1384R007","1384R008","1384R009","1384R010","1384R011","1384R012","1384R013","1384R014","1384R015","1384R016","1384R017","1384R018"
        ]
      }
    },
    {
      "code": "Inkomstkomponenter",
      "selection": {
        "filter": "item",
        "values": [
          "240"
        ]
      }
    },
    {
      "code": "Kon",
      "selection": {
        "filter": "item",
        "values": [
          "1",
          "2"
        ]
      }
    },
    {
      "code": "ContentsCode",
      "selection": {
        "filter": "item",
        "values": [
          "000005FW"
        ]
      }
    }
  ],
  "response": {
    "format": "json"
  }
}
            
            response = requests.post("https://api.scb.se/OV0104/v1/doris/sv/ssd/START/HE/HE0110/HE0110I/Tab2InkDesoN", json=payload)

            data = response.json()
            print('Response received from SCB')
            # Prepare the data for batch insertion
            batch_data = []
            for entry in data['data']:
                key = entry['key']
                values = entry['values']
                
                regso = key[0]
                kon = key[2]
                ar = key[3]
                nettoinkomst_tkr = float(values[0])  
                
                batch_data.append((regso, kon, ar, nettoinkomst_tkr))
                
        except Exception as e:
            print(f"Failed to fetch or insert data: {e}")
            exit(1)

        # Insert data into BigQuery table
        table_id = f"{dataset_name}.{table_name}"
        table = client.get_table(table_id)
        errors = client.insert_rows(table, batch_data)
        
        if errors == []:
            st.write("New rows have been added.")
        else:
            st.write(f"Encountered errors while inserting rows: {errors}")

    except Exception as e:
        st.write(f"Failed to insert rows: {e}")


