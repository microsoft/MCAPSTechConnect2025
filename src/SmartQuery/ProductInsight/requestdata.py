from pydantic import BaseModel

class RequestData(BaseModel):  
    RequestId: str='NA'
    QueryType: str='NA'
    Query: str='NA'
    Language: str='English'
    UserId: str='NA'
    CarModel: str='NA'
    FuelType: str='NA'
    Infotainment: str='NA'

    