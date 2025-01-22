import json
import logging  
from typing import Any, Dict  
import azure.functions as func  
from ProductInsight import ProductQueryProcessor, RequestData  
from Config import AppConfig  
from askai_core.telemetry import CosmosUtility  
from askai_core.common import CacheFactory, CacheType  
from askai_core.common import OpenAIUtility  
from askai_core.content_insight import VectorDbIndexer, IndexType  
import uuid  
from datetime import datetime,timezone
import time
  
  
async def main(req: func.HttpRequest) -> func.HttpResponse:  
    logging.info('Product Insight Request Triggered.')  
    try:  
        request: Dict[str, Any] = req.get_json()  
        request_data = RequestData(**request)  
        
        config = AppConfig.get_instance()  
        cache = CacheFactory.get_cache(  
            cachetype=CacheType.REDIS,  
            redis_host=config.redis_host,  
            redis_password=config.redis_password
        )  
        openaiutility = OpenAIUtility(  
            openai_api_base=config.openai_api_base,  
            openai_api_key=config.openai_api_key,  
            openai_api_version=config.openai_api_version,  
            cosmos_container_name=config.askai_analytics_cosmos_db_container,  
            cosmos_database_name=config.askai_cosmos_db_name,  
            cosmos_endpoint=config.askai_cosmos_db_endpoint  
        )  
        searchindexer = VectorDbIndexer.get_index(  
            index_type=IndexType.AZCOGNITIVESEARCH,  
            azure_cognitive_search_service_url=config.azure_cognitive_search_service_url,  
            index_name=config.azure_cognitive_search_automotive_index_name,  
            api_key= config.azure_cognitive_admin_key,  
            openai_utility=openaiutility  
        )  

        cosmos_utility = CosmosUtility(  
            endpoint=config.askai_cosmos_db_endpoint,  
            key=None,  
            database_name=config.askai_cosmos_db_name,  
            container_name=config.askai_analytics_cosmos_db_container  
        ) 

        cosmos_utility_masterdata = CosmosUtility(  
            endpoint=config.askai_cosmos_db_endpoint,  
            key=None,  
            database_name=config.askai_cosmos_db_name,  
            container_name="msilmasterdata" 
        ) 

        knowledge_base_query_processor = ProductQueryProcessor(  
            requestdata=request_data,  
            config=config,  
            cache=cache, 
            cosmosutility=cosmos_utility_masterdata, 
            openaiutility=openaiutility,  
            searchindexer=searchindexer,
        )  
  
        start_time = datetime.now()
        query_response = await knowledge_base_query_processor.process_query()  
        end_time =  datetime.now()
        time_difference_ms = (end_time - start_time).total_seconds() * 1000
        raw_response_string = json.dumps(query_response, indent=4)
        await insert_analytics_data_cosmos( 
            cosmos_utility=cosmos_utility, 
            request_id=request_data.RequestId,
            user_id=request_data.UserId,
            language=request_data.Language, 
            query_type=request_data.QueryType, 
            query=request_data.Query,
            response=raw_response_string,
            response_time_ms=time_difference_ms
        )  
        return func.HttpResponse(query_response, status_code=200)
    except ValueError as e:
            logging.error(str(e))
            return func.HttpResponse("Sorry, I am not able to answer your question at this moment based on the context provided.", status_code=500)  
    except Exception as e:  
        logging.error(f"Error in Product Insight Request: {str(e)}")  
        return func.HttpResponse("Error in process of request", status_code=400)  
    
def convert_to_utc_iso(dt):
        # Convert it to UTC
        dt = dt.astimezone(timezone.utc)
        # Convert it to ISO 8601 forma
        iso_format = dt.isoformat()
        return iso_format
  
  
async def insert_analytics_data_cosmos(cosmos_utility: CosmosUtility, request_id: str, user_id: str,language: str, query_type: str, query: str, response_time_ms: float = 0, response: str=""):  
    app_config = AppConfig.get_instance()  
    try:  
        data_to_insert = {  
            "id": str(uuid.uuid4()),
            "Category": "App",
            "RequestId": request_id,
            "UserId": user_id,  
            "Language": language,
            "ModuleName": app_config.module_name,
            "QuerType": query_type,
            "Query": query, 
            "ResponseTimeMs": response_time_ms,
            "Response": response,
            "CreatedDateTime": str(convert_to_utc_iso(datetime.now()))
        }  
        cosmos_utility.create_item(data_to_insert)  
    except Exception as e:  
        logging.error(f"Error inserting analytics data: {str(e)}")  
