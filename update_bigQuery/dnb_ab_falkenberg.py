import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import io

# Create a credentials object using the service account info from the secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials)

# Create BigQuery Dataset and Table
dataset_name = "dnb_data"
table_name = "dnb_ab_falkenberg"

# Streamlit App
st.title("CSV Upload to BigQuery")

# Function to create BigQuery table
def create_bigquery_table(client, dataset_name, table_name, schema):
    dataset_id = f"{client.project}.{dataset_name}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "EU"
    
    try:
        dataset = client.create_dataset(dataset, exists_ok=True)
        st.write(f"Dataset created/exists: {dataset_id}")
    except Exception as e:
        st.write(f"Error creating dataset: {e}")
        return

    table_id = f"{dataset_id}.{table_name}"
    
    try:
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table, exists_ok=True)
        st.write(f"Table created/exists: {table_id}")
    except Exception as e:
        st.write(f"Error creating table: {e}")

# Define schema for the table
schema = [
    bigquery.SchemaField("bokslutsar", "STRING"),
    bigquery.SchemaField("omsattning", "FLOAT"),
    bigquery.SchemaField("anstallda", "INTEGER"),
    bigquery.SchemaField("arbetstallen", "INTEGER"),
    bigquery.SchemaField("lonsamhetsindex", "FLOAT"),
    bigquery.SchemaField("bransch_grov", "STRING"),
    bigquery.SchemaField("bransch_fin", "STRING"),
    bigquery.SchemaField("foretag", "STRING"),
    bigquery.SchemaField("org_nummer", "STRING"),
    bigquery.SchemaField("totalt_kapital", "FLOAT"),
    bigquery.SchemaField("eget_kapital", "FLOAT"),
    bigquery.SchemaField("soliditet", "FLOAT"),
    bigquery.SchemaField("resultat", "FLOAT"),
    bigquery.SchemaField("rorelsemarginal", "FLOAT"),
]

# Create table
if st.button('Create BQ table'):
    create_bigquery_table(client, dataset_name, table_name, schema)

# Define your BigQuery schema column names
column_names = [
    "bokslutsar", "omsattning", "anstallda", "arbetstallen",
    "lonsamhetsindex", "bransch_grov", "bransch_fin", "foretag", 
    "org_nummer", "totalt_kapital", "eget_kapital", "soliditet", 
    "resultat", "rorelsemarginal"
]

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    # Read data from the uploaded CSV file
    # If your CSV includes headers, you can omit the 'names' parameter
    dataframe = pd.read_csv(uploaded_file, names=column_names, header=None)

    # Replace "-" with None in all columns
    dataframe.replace('-', None, inplace=True)

    # Load CSV data to BigQuery
    table_id = f"{dataset_name}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        skip_leading_rows=1,  # Skip the header row if your CSV includes it, else set to 0
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    try:
        load_job = client.load_table_from_dataframe(
            dataframe, table_id, job_config=job_config
        )
        load_job.result()  # Wait for the job to complete

        if load_job.errors:
            st.write("Errors during load job:")
            for error in load_job.errors:
                st.write(error)
        else:
            st.write("Upload completed successfully.")

    except Exception as e:
        st.write(f"Failed to upload CSV to BigQuery: {e}")

        # Additional debugging information
        if hasattr(e, 'errors') and e.errors:
            st.write("Detailed errors:")
            for error in e.errors:
                st.write(error)