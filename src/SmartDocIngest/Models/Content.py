from pydantic import BaseModel
from typing import Optional

class Content(BaseModel):
    Data: Optional[str] = ""
    Path: Optional[str] = ""
    OriginalContentType: Optional[str]= ""
    FileName: str = ""
    FileUrl: Optional[str] = ""
    Identifier: str = ""
    LastModified: str = ""
    Keywords: str = ""
    ChunkSize: Optional[str] = ""
    Description: Optional[str] = ""
    ContentType: Optional[str] = ""
    ExpiritationDate: Optional[str] = ""
    Status: Optional[str] = ""
    TargetAudience: Optional[str] = ""
    IngestedArticleUrl: Optional[str] = ""