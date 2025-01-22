from datetime import datetime 
import logging
import re  
from askai_core.Utility.functions import log_execution_time, generate_cache_key  
from askai_core.common import OpenAIUtility, AskAIPromptManager  
from askai_core.common import BaseCacheWrapper  
from askai_core.content_insight import VectorDbIndexer  
from ProductInsight.requestdata import RequestData  
from Config import AppConfig
from askai_core.telemetry import CosmosUtility  
from typing import Any, List, Dict, Optional  
import os  
import json
import asyncio
import ast
import re
import time
  
class ProductQueryProcessor:  
    def __init__(self,  
                 requestdata: RequestData,  
                 config: AppConfig, 
                 cache: BaseCacheWrapper, 
                 cosmosutility: CosmosUtility, 
                 openaiutility: OpenAIUtility,  
                 searchindexer: VectorDbIndexer
                 ):  
        self.requestdata = requestdata  
        self.config = config  
        self.cache = cache
        self.cosmosutility = cosmosutility 
        self.openaiutility = openaiutility 
        self.searchindexer = searchindexer  
    
    @log_execution_time  
    async def process_query(self) -> str:  
        try:  
            logging.info('Product Insight Request Triggered.-'+ self.requestdata.Query)
            query = self.requestdata.Query
            query_type = self.requestdata.QueryType.lower()
            user_id = self.requestdata.UserId
            car_model = self.requestdata.CarModel
            
            filter_dict, filterimages_dict, filtervideos_dict = self._generate_filter_dicts(query_type, car_model)
            
            logging.info(f'Query: {query}, User Id: {user_id}, Car Model: {car_model}, Query Type: {query_type}') 
            cache_key = generate_cache_key(user_id, f'Product_X_{query}_{query_type}_{car_model}', False)
            cache_response = self._get_cache_response(cache_key)
            if cache_response:
                logging.info(f'Response found in cache for query: {cache_response}')
                return cache_response  
            product_images = None
            product_videos = None
            product_documents = None
            if 'recommend' in query_type:
                arenadata=await self.fetch_arena_data(query_type, f"{query}. Include only Maruti Suzuki Arena Channel Cars", user_id, filter_dict, self.requestdata),
                logging.info(f"product_response_arena: {arenadata}")
                
                time.sleep(2)
                logging.info(f'sleeping for 2 sec: ')
                
                nexadata=await self.fetch_nexa_data(query_type, f"{query}. Include only Maruti Suzuki Nexa Channel Cars", user_id, filter_dict, self.requestdata)
                logging.info(f"product_response_nexa: {nexadata}")
                product_documents = f"Here are Cars from Maruti Suzuki Arena Channel -{arenadata} \n Here are cars from Maruti Suzuki Nexa Channel- {nexadata}"
            else:

                product_documents = await self._get_relevant_documents(query, user_id, filter_dict) 
            logging.info(f"product_documents: {product_documents}")
            is_combined_response = True if 'recommend' in query_type else False
            if filterimages_dict is not None:
                product_images = await self._get_relevant_documents(query, user_id, filterimages_dict)  
            if filtervideos_dict is not None:
                product_videos = await self._get_relevant_documents(query, user_id, filtervideos_dict)
            if not product_documents:
                logging.info(f"product_documents is None")

                raise ValueError("No relevant content found for query")
            logging.info(f"product_images- product_videos {product_images}- {product_videos}")
            logging.info(f"product_documents -  {product_documents}")
            
            product_images = product_images if product_images is not None else ""  
            product_videos = product_videos if product_videos is not None else "" 
            result = await self._generate_response(query_type,  query, product_documents, product_images, product_videos, self.requestdata.Language,is_combined_response)  
            result=json.dumps(result)
            logging.info(f"Response generated for query: {query}- {result}")

            if result:
                # Get Cdnurl
                result = result.strip()
                # Remove any backslashes not part of an escape sequence
                result = re.sub(r'\\(?![nrt\\"\'b])', r'\\\\', result)
                # Replace escape sequences like \n, \t with space or appropriate character
                result = result.replace(r"\\n", " ") # Replace \n with a space
                result = result.replace(r"\\t", " ") # Replace \t with a space
                # Convert double backslashes to single (to address issues where backslashes are improperly escaped)
                result = result.replace(r"\\\\", r"\\")
                # Handle any remaining unescaped characters
                result = re.sub(r'[\x00-\x1F]+', '', result)
                
                # Now try to load the cleaned string into a JSON object
                data = json.loads(result)
                cdnUrl = ""
                fileurl = ""
                if data.get("Source"):
                    fileurl = data.get("Source")
                    if('brochure' in query_type):
                        logging.info(fileurl)
                        cdnurlquery ="SELECT d.CdnUrl FROM c JOIN d IN c.cdn_mapping_master WHERE d.FileUrl = @fileurl"
                        parameters = [{"name": "@fileurl", "value": fileurl}]
                        items = self.read_data_from_cosmos(cdnurlquery,parameters)
                        logging.info("cosmos db call done for cdnurl")
                        if items is not None and len(items) > 0:
                            for item in items:
                                cdnUrl = item.get('CdnUrl')
                                data["AssociatedCdnLink"] = cdnUrl
                data["AssociatedCdnLink"] = cdnUrl
                final_result = json.dumps(data, indent=4)
                if fileurl and fileurl in final_result:
                    service_response = final_result.replace(fileurl, cdnUrl)
                else:
                    service_response = final_result
                self._cache_response(cache_key, service_response)
                logging.info(f'Adding to cache: {service_response}')

                return service_response
            else:
                return None
        except ValueError as e:
            logging.error(e)
            logging.error("No relevant content found for query: " + query)  
            return None 
        except Exception as e:  
            logging.error("Error in processing query"+ str(e))  
            return None
        
    def read_data_from_cosmos(self,query,parameters):
        try:
            return list(self.cosmosutility.container.query_items(query=query,parameters=parameters,enable_cross_partition_query=True))
        except Exception as e:
            logging.error(f"Error in read_data_from_cosmos function: {str(e)}")
            raise
    
    async def fetch_arena_data(self, query_type, query, user_id, filter_dict, requestdata):
        try:
            if 'recommend' in query_type:
                arena_filter_dict = filter_dict.copy()
                arena_filter_dict['keyword'] = 'BrandType-Arena'
                logging.info(f"arena_filter_dict- {arena_filter_dict}")

                product_documents_arena = await self._get_relevant_documents(query, user_id, arena_filter_dict)
                logging.info(f"product_documents_arena_response from search- {product_documents_arena}")
                
                product_documents_arena_response = await self._generate_response(query_type, query, product_documents_arena, None, None, requestdata.Language)
                logging.info(f"product_documents_arena_response from open ai- {product_documents_arena_response}")
                
                if product_documents_arena_response:
                    if isinstance(product_documents_arena_response, dict) and 'TextResponse' in product_documents_arena_response:
                        return product_documents_arena_response['TextResponse']
                    else:
                        return ''
                else:
                    return ''  # Return empty string if no response

            else:
                logging.info("Query type is not 'recommend'. Skipping Arena fetch.")
                return ''  # Return empty string if 'recommend' is not in query_type

        except Exception as e:
            logging.error(f"Error processing Arena response: {e}")
            return ''  # Return empty string if an error occurs

    async def fetch_nexa_data(self,query_type, query, user_id, filter_dict, requestdata):
        try:
            nexa_filter_dict = filter_dict.copy()
            nexa_filter_dict['keyword'] = 'BrandType-Nexa'

            product_documents_nexa = await self._get_relevant_documents(query, user_id, nexa_filter_dict)
            logging.info(f"product_documents_nexa response from ai search- {product_documents_nexa}")
            
            product_documents_nexa_response = await self._generate_response(query_type, query, product_documents_nexa, None, None, requestdata.Language)
            logging.info(f"product_documents_nexa response from open ai- {product_documents_nexa_response}")

            if product_documents_nexa_response:
                if isinstance(product_documents_nexa_response, dict) and 'TextResponse' in product_documents_nexa_response:
                    return product_documents_nexa_response['TextResponse']
                else:
                    return ''
            else:
                return ''  # Return empty string if no response

        except Exception as e:
            logging.error(f"Error processing Nexa response: {e}")
            return ''  # Return empty string if an error occurs

    def _generate_filter_dicts(self, query_type: str, car_model: str) -> tuple:
        filter_dict = None
        filterimages_dict = None
        filtervideos_dict = None
        query_type=query_type.lower()
        logging.info(f'query_type - { query_type}')
        logging.info(f'car_model - { car_model}')

        if car_model != 'NA':
            if 'alto' in car_model.lower():
                car_model='ALTO'
            if 'fronx' in car_model.lower():
                car_model='FRONX'
            if 'xl6' in car_model.lower():
                car_model='XL6'
            car_model = car_model.replace(" ", "").replace("-","")
            
            filter_dict = {"ModelName": car_model}
            if 'comparison' in query_type:
                filter_dict["DocumentType"] = "TechnicalSpecifications"
            if 'tech' in query_type or 'modelvarient' in query_type or 'feature' in query_type:
                filter_dict["DocumentType"] = "TechnicalSpecifications"    
            elif 'brochure' in query_type:
                filter_dict["DocumentType"] = "Brochure"
            elif 'manual' in query_type:
                filter_dict["DocumentType"] = "OwnerManual"
                fuel_type = getattr(self.requestdata, 'FuelType', None)
                logging.info(f'fuel_type- {fuel_type}')
                if fuel_type:
                    fuel_type = fuel_type.lower()
                    match fuel_type:
                        case 'petrol':
                            filter_dict["keyword"] = 'FuelType-Petrol'
                        case 'cng':
                            filter_dict["keyword"] = 'FuelType-CNG'
                        case _:
                            logging.info(f"Unknown FuelType: {fuel_type}")
                infotainment = getattr(self.requestdata, 'Infotainment', None)
                logging.info(f'Infotainment- {infotainment}')
                if infotainment:
                    infotainment = infotainment.lower()
                    match infotainment:
                        case 'audio':
                            filter_dict["keyword"] = 'Infotainment-Audio'
                        case _:
                            logging.info(f"Unknown Infotainment: {infotainment}")
            elif 'accessories' in query_type:
                filter_dict["DocumentType"] = "Accessories"
            elif 'recommendation' in query_type or 'selection' in query_type:
                filter_dict["DocumentType"] = "CarSelection"
                filter_dict ["ModelName"]= "ALL"   
            elif 'color' in query_type:
                filter_dict["DocumentType"] = "Colors" 
            else:
                filter_dict["exclude_DocumentType"] = "Images"
                filter_dict["DocumentType"] = "TechnicalSpecifications"       


            if 'brochuredownload' not in query_type:
                filterimages_dict = {"ModelName": car_model, "DocumentType": "Images"}
                filtervideos_dict = {"ModelName": car_model, "DocumentType": "Videos"}
                
        elif 'recommendation' in query_type or 'selection' in query_type:
                filter_dict = {"ModelName": "ALL"}
                filter_dict["DocumentType"] = "CarSelection"
        elif 'tech' in query_type or 'modelvarient' in query_type or 'feature' in query_type:
                filter_dict = {"ModelName": "ALL"}
                filter_dict["DocumentType"] = "TechnicalSpecifications"            
        elif 'color' in query_type:
                filter_dict = {"ModelName": "ALL"}
                filter_dict["DocumentType"] = "Colors"       
        else:
            filter_dict = {"exclude_DocumentType": "Images"}
            filter_dict["DocumentType"] = "CarSelection"    
            filter_dict ["ModelName"]= "ALL"   


        if 'techSpec' in query_type:
            filter_dict = {"DocumentType": "TechnologyDocuments"}
        elif 'servicepackage' in query_type:
            filter_dict = {"DocumentType": "ServiceDocuments"}
        logging.info("Filter Dictionary: %s", filter_dict)
        logging.info("Filter Images Dictionary: %s", filterimages_dict)
        logging.info("Filter Videos Dictionary: %s", filtervideos_dict)
        
        return filter_dict, filterimages_dict, filtervideos_dict
  
    def _get_cache_response(self, cache_key: str) -> Optional[str]: 
        try: 
            return self.cache.readstr_from_cache(cache_key)  
        except Exception as e:  
            logging.error(str(e))  
            return None
  
    async def _get_relevant_documents(self, query: str, user_id: str,filter_fields:Dict) -> List[Dict[str, Any]]:  
        try:
            logging.info("filter_fields: %s", filter_fields)
            if 'DocumentType' in filter_fields and (filter_fields["DocumentType"] =="TechnicalSpecifications" or filter_fields["DocumentType"] =="Colors") or filter_fields["DocumentType"] == "CarSelection":
                logging.info(f'filter_fields contains techspec or colors- {filter_fields["DocumentType"]}')

                data = await self.searchindexer.get_relevant_content(query, embedding_deloyment_name=self.config.openai_embedding_deployment_name, user_id=user_id,fields= ["FileName","DocumentId"],filter_fields=filter_fields)  
                logging.info(f"data: {data}")
                match = re.search(r'DocumentId:\s*(.*?)(?:,|$)', data)
                if match:
                    documentId = match.group(1)
                    logging.info(f'DocumentId:{ documentId}')
                    return await self.searchindexer.get_all_content_chunks(documentId)  

                else:
                    logging.info(f'DocumentId not found')
            else:
                return await self.searchindexer.get_relevant_content(query, embedding_deloyment_name=self.config.openai_embedding_deployment_name, user_id=user_id,fields= ["FileName","Content"],filter_fields=filter_fields)  

        except Exception as e:
            logging.error(f'error in fetching relevent documents - {e}')
            return None
  
    async def _generate_response(
    self,
    query_type: str,
    query: str,
    documents: List[Dict[str, Any]],
    image_documents: List[Dict[str, Any]],
    video_documents: List[Dict[str, Any]],
    language: str = None,
    is_combined_response: bool = False,
) -> str:
        logging.info(f"Generating response for query_type: {query_type} & query: {query}")
        if not is_combined_response:
            filepath = os.path.join(os.path.dirname(__file__), 'prompt.json')
            context_prompt_manager: AskAIPromptManager = await AskAIPromptManager.load(
                source='local', prompt_file_path=filepath, cosmos_db_processor=None
            )
            if 'recommend' in query_type or 'selection' in query_type:
                logging.info(f"Generating response from recommend prompt for query_type: {query_type} & query: {query}")

                PRODUCT_PROMPT_TEMPLATE = await context_prompt_manager.get_prompt(
                    'PRODUCT_CARRECOMMENDPROMPT_TEMPLATE', os.path.dirname(__file__)
                )
            else:
                PRODUCT_PROMPT_TEMPLATE = await context_prompt_manager.get_prompt(
                    'PRODUCT_PROMPT_TEMPLATE', os.path.dirname(__file__)
                )

            PRODUCT_PROMPT_TEMPLATE_IMAGE = await context_prompt_manager.get_prompt(
                'PRODUCT_PROMPT_TEMPLATE_IMAGE', os.path.dirname(__file__)
            )
            PRODUCT_PROMPT_TEMPLATE_VIDEO = await context_prompt_manager.get_prompt(
                'PRODUCT_PROMPT_TEMPLATE_VIDEO', os.path.dirname(__file__)
            )

            system_prompt = (
                f"Current date is {datetime.now().strftime('%d %B %Y')}\n"  
                f"You must generate the response in {language} language.\n"
                f"{PRODUCT_PROMPT_TEMPLATE}"
            )
            logging.info(f"system_prompt: {system_prompt}")

            system_prompt_video = (
                f"Current date is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"You must generate the response in {language} language.\n"
                f"{PRODUCT_PROMPT_TEMPLATE_VIDEO}"
            )

            text_prompt = [
                {"role": "system", "content": f"{system_prompt}{documents}"},
                {"role": "user", "content": f"Question: {query}"},
            ]

            # Initialize tasks for image and video only if documents are provided
            image_response_task = None
            video_response_task = None

            if image_documents:
                logging.info(f"image_documents exists")

                system_prompt_image = (
                    f"Current date is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"You must generate the response in {language} language.\n"
                    f"{PRODUCT_PROMPT_TEMPLATE_IMAGE}"
                )
                image_prompt = [
                    {"role": "system", "content": f"{system_prompt_image}{image_documents}"},
                    {"role": "user", "content": f"Question: {query}"},
                ]
                image_response_task = self.openaiutility.generate_completion(
                    prompt=image_prompt,
                    gpt_deployment_name=self.config.openai_gpt_deployment_name,
                    ai_assistant=self.config.module_name,
                    conversation_id=self.requestdata.RequestId,
                    apimendpoint=self.config.apim_gateway_url,
                    apimsubscriptionkey=self.config.apim_subscription_key,
                    api_version=self.config.openai_api_version
                )

            if video_documents:
                logging.info(f"video_documents exists: {video_documents}")

                video_prompt = [
                    {"role": "system", "content": f"{system_prompt_video}{video_documents}"},
                    {"role": "user", "content": f"Question: {query}"},
                ]
                video_response_task = self.openaiutility.generate_completion(
                    prompt=video_prompt,
                    gpt_deployment_name=self.config.openai_gpt_deployment_name,
                    ai_assistant=self.config.module_name,
                    conversation_id=self.requestdata.RequestId,
                    apimendpoint=self.config.apim_gateway_url,
                    apimsubscriptionkey=self.config.apim_subscription_key,
                    api_version=self.config.openai_api_version
                )

            text_response_task = self.openaiutility.generate_completion_json_format(
                prompt=text_prompt,
                gpt_deployment_name=self.config.openai_gpt_deployment_name,
                max_token= 4000,
                ai_assistant=self.config.module_name,
                conversation_id=self.requestdata.RequestId,
                apimendpoint=self.config.apim_gateway_url,
                apimsubscriptionkey=self.config.apim_subscription_key,
                api_version=self.config.openai_api_version
            )

            # Await tasks using asyncio.gather
            responses = await asyncio.gather(
                text_response_task,
                image_response_task if image_response_task else asyncio.sleep(0),
                video_response_task if video_response_task else asyncio.sleep(0),
            )

            text_response, image_response, video_response = responses[0], responses[1], responses[2]

            logging.info(f"text_response: {text_response}")

            # Extract properties from the JSON response of text_response_task
            try:
                text_response_data = json.loads(text_response, strict=False)
            except (ValueError, SyntaxError) as e:
                logging.error(f"Failed to parse text_response as JSON: {e}")
                text_response_data = {}

            text_response_text = text_response_data.get("TextResponse", "")
            text_response_source = text_response_data.get("Source", "")

            # Log responses for debugging
            logging.info(f"text_response_text: {text_response_text}")
            logging.info(f"image_response: {image_response}")
            logging.info(f"video_response: {video_response}")
            logging.info(f"Source: {text_response_source}")

            # Combine responses into the final output
            combined_response = {
                "TextResponse": text_response_text,  # Use "textresponse" property
                "AssociatedImageLink": image_response,
                "AssociatedVideoLink": video_response,
                "Source": text_response_source,  # Use "source" property
            }

            return combined_response
        else:
            combined_response = {
                "TextResponse": documents,  # Use "textresponse" property
                "AssociatedImageLink": None,
                "AssociatedVideoLink": None,
                "Source": None,  # Use "source" property
            }

            return combined_response

  
    def _cache_response(self, cache_key: str, result: str):  
        self.cache.write_to_cache(cache_key, result, 3600)  
