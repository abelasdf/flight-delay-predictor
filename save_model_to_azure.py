import os
from azure.storage.blob import BlobServiceClient
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--connection_string", help="Azure Storage Connection String")
args = parser.parse_args()

connection_string = args.connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")

container_name = "flightmodel-1"  # kannst du bei Bedarf anpassen
blob_name = "flight_delay_model.pkl"
local_model_path = "model/flight_delay_model.pkl"

blob_service_client = BlobServiceClient.from_connection_string(connection_string)

try:
    container_client = blob_service_client.create_container(container_name)
    print(f"Container {container_name} erstellt.")
except Exception as e:
    print(f"Container {container_name} bereits vorhanden oder Fehler: {e}")

blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

with open(local_model_path, "rb") as data:
    blob_client.upload_blob(data, overwrite=True)

print(f"Modell {blob_name} erfolgreich in Azure Blob Storage hochgeladen.")