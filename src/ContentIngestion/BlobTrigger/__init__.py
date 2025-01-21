import json
import logging
import os
import aiohttp
import azure.functions as func
import base64
import uuid
from Configuration.Settings import Settings
from urllib.parse import urlparse
from Processors.IngestionProcessor import IngestionProcessor

class BlobTriggerIngestion:
    
    def __init__(self):    
        self._settings = Settings()    

    async def process_query(self,myblob: func.InputStream):    
    
        try:
            logging.info(f"Blob trigger function processed a blob. Name: {myblob.name}")
            blob_content = myblob.read()
            try:
                
                blob_content_base64 = base64.b64encode(blob_content).decode('utf-8')
            except Exception as e:
                logging.error(f"Error decoding JSON from blob content: {e}")
                return
            
            properties = {
                'blob_type': 0,
                'content_type': myblob.blob_properties.get('ContentType'),
                'etag': myblob.blob_properties.get('ContentHash'),
                'last_modified': myblob.blob_properties.get('LastModified'),
                'Modified': myblob.blob_properties.get('LastModified'),
                'length': myblob.blob_properties.get('ContentLength'),
                'Title': myblob.name,
                'Created'  : myblob.blob_properties.get('CreatedOn'),
                'FullPath': myblob.uri,
            }
            
            req_body = {
                "Operation": "Insert",
                "DataSource": "blob",
                "DocumentId": str(uuid.uuid4()),
                "Properties": properties,
                "Fields": {
                    "Data": blob_content_base64,
                    "ContentType": myblob.blob_properties.get('ContentType'),
                    "FileName": os.path.basename(myblob.name),
                    "ChunkSize": '10240',
                    "FileUrl": myblob.uri,
                    "DocumentType": "TechConnect",
                    "LastModified": myblob.blob_properties.get('LastModified'),
                    "Identifier": str(uuid.uuid4())
                }
            }
            current_directory = os.path.dirname(__file__)
            # Navigate to the Models directory
            models_directory = os.path.join(current_directory, '..', 'Models')
            # Path to fields.json
            fields_json_path = os.path.join(models_directory, 'fields.json')

            processor = IngestionProcessor(settings=Settings(),fieldsPath=fields_json_path)
            
            result = 'Unable to process request at this time'
            match(req_body.get('Operation')):  
                case "Insert":  
                    result = 'True' if processor.process(req_body) else 'False'  
                case __:  
                    logging.warning("Invalid Operation Requested")  
                    result = "Invalid Operation"  

            # Store result in Azure Table/Queue or log it
            logging.info(f"Processing Result: {result}")
            
            return None
        
        except Exception as e:  
            logging.error(msg=str(e), exc_info=e)
            raise
    
blobTriggerIngestion = BlobTriggerIngestion()    
    
async def main(myblob: func.InputStream):  
    return await blobTriggerIngestion.process_query(myblob)    
