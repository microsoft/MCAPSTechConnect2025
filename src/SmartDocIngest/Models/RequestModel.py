from pydantic import BaseModel
from Models.Content import Content
from typing import Optional
from Models.DataSources import DataSources
from Models.DocumentTypes import DocumentTypes

class RequestModel(BaseModel):
    Operation: str = "Insert"
    DataSource: DataSources = ""
    DocumentType: DocumentTypes = ""
    DocumentId: str = ""
    Fields: Content
    Properties: Optional[dict] = {}