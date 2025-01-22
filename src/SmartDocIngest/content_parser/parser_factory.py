from typing import Optional

from askai_core.common import AzureBlobStorageManager
from askai_core.common import OpenAIUtility



class ParserFactory:
    @staticmethod
    def create_parser(file_content: bytes, file_extension: str, azure_form_recognizer_endpoint: str = None, azure_form_recognizer_key: str = None, openai_utility: OpenAIUtility = None, azure_blob_storage_manager: AzureBlobStorageManager = None) -> Optional['BaseParser']:
        if file_extension == 'pdf' or file_extension == 'application/pdf':
            from askai_core.content_parser.pdf_parser import PDFParser
            return PDFParser(file_content, azure_form_recognizer_endpoint, azure_form_recognizer_key, openai_utility, azure_blob_storage_manager)
        else:
            return None

