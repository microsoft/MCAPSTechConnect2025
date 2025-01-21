import base64
import uuid
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.identity import DefaultAzureCredential

from datetime import datetime, timedelta

from io import BytesIO
import logging

class AzureBlobStorageManager:
    """
    A class that provides functionality for saving and uploading either bytes or a file from a temp location to a blob and generate a SAS URL.
    """
    def __init__(self, account_name, account_key, container_name, sas_url_expiry_window):
        self.account_name = account_name
        self.account_key = account_key
        self.container_name = container_name
        self.sas_url_expiry_window = sas_url_expiry_window
        self.blob_name = ""

    def upload_to_blob(self, content: bytes = None, local_path: str = None, file_format: str = 'png',return_sas_url=False) -> str:
        """
        Uploads content to Azure Blob Storage and returns a SAS URL.

        :param content: Bytes to be uploaded.
        :param local_path: Local file path to be uploaded.
        :param file_format: File format (default is 'png').
        :return: SAS URL for the uploaded blob.
        """
        try:
            if not content and not local_path:
                raise ValueError("Either content or local_path must be provided.")
            
            guid = uuid.uuid4()
            self.blob_name = f"askai_{guid}.{file_format}"
            logging.info(f"Uploading blob with name: {self.blob_name}")
            blob_service_client = self.get_blob_client()
            
            container_client = self._get_or_create_container(blob_service_client)

            blob_client = container_client.get_blob_client(self.blob_name)
            logging.info("Blob client created successfully.")
            # Check if the blob already exists
            if not blob_client.exists():
                blob_client.upload_blob(BytesIO(content) if content else open(local_path, "rb").read())

            if (return_sas_url):
                sas_url = self._generate_sas_url(blob_client)
                logging.info(f"Blob uploaded successfully. SAS URL: {sas_url}")
                return sas_url
                
            logging.info(f"Blob uploaded successfully.")
            return self.blob_name
        except Exception as e:
            logging.error(f"Error while processing the blob request: {str(e)}")  
            raise e

    def get_blob_client(self):
        account_url = f"https://{self.account_name}.blob.core.windows.net"
        credential = self.account_key if self.account_key else DefaultAzureCredential()
        return BlobServiceClient(account_url=account_url, credential=credential)

    def _get_or_create_container(self, blob_service_client):
        container_client = blob_service_client.get_container_client(self.container_name)
        if not container_client.exists():
            container_client.create_container()
        return container_client

    def _generate_sas_url(self, blob_client):
        sas_expiry = datetime.utcnow() + timedelta(minutes=int(self.sas_url_expiry_window))
        sas_permissions = BlobSasPermissions(read=True)
        sas_token = generate_blob_sas(
            blob_client.account_name,
            self.container_name,
            self.blob_name,
            account_key=blob_client.credential.account_key,
            permission=sas_permissions,
            expiry=sas_expiry
        )
        return blob_client.url + "?" + sas_token

    def download_from_blob(self, blob_name):
        """
        Downloads content from Azure Blob Storage and content in base 64.

        :param content: blob name.
        """
        try:
            blob_service_client = self.get_blob_client()
            container_client = self._get_or_create_container(blob_service_client)
            blob_client = container_client.get_blob_client(blob_name)
            logging.info("Blob client created successfully.")
            # Download the blob content
            blob_content = blob_client.download_blob().content_as_bytes()

            # Convert the blob content to base64 format
            base64_content = base64.b64encode(blob_content).decode('utf-8')

            return base64_content
        except Exception as e:
            logging.error(f"Error while downloading the blob: {str(e)}")
            raise e