from typing import Optional  
from pydantic import BaseModel  

class RequestData(BaseModel):  
    UserId: str = "NA"  
    UserEmail: Optional[str] = "NA"
    UserName:Optional[str]="NA"
    Query: str = "NA"  
    RequestId: str = "NA"  
    IsShowPlanOnly: Optional[bool] = False  # Optional but defaults to False  

