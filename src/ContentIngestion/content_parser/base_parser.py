from typing import Tuple
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from askai_core.common import AzureBlobStorageManager
from askai_core.common import OpenAIUtility


class BaseParser:

    def __init__(self, file_content: bytes,azure_form_recognizer_endpoint:str,azure_form_recognizer_key:str, openai_utility: OpenAIUtility, azure_blob_storage_manager: AzureBlobStorageManager, process_image: bool=False):
        self.file_content = file_content
        self.documentAnalysisClient=None
        if azure_form_recognizer_endpoint and azure_form_recognizer_key:
            self.documentAnalysisClient=  DocumentAnalysisClient(
                endpoint=azure_form_recognizer_endpoint,
                credential=AzureKeyCredential(azure_form_recognizer_key)
            )
        self.openai_utility = openai_utility
        self.storage_manager = azure_blob_storage_manager
        self.process_image = process_image

    def extract_text(self) :
        raise NotImplementedError("Subclasses must implement extract_text method.")
    
    def extract_table(self) :
        raise NotImplementedError("Subclasses must implement extract_table method.")
    
    def extract_images(self) :
        raise NotImplementedError("Subclasses must implement extract_images method.")
