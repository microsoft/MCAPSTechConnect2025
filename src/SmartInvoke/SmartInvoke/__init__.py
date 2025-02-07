import asyncio
import json  
import os  
import logging  
from datetime import datetime, timezone  
from typing import Any, Dict, Optional, Tuple
import azure.functions as func  
import aiofiles  
from tabulate import tabulate
from Invoker import SmartInvoker  
from Config import AppConfig  
from common import RequestData  
import re
from common.functions import count_tokens
from common.openai_utils import OpenAIUtility

PROMPT_LIBRARY_DIR = 'prompt_library'  
AGENT_LIBRARY_DIR = 'agent_library'  
SUGGESTION_PROMPT_FILE = 'query_suggestion_prompt.txt'  
CONFIG_FILE = 'agent_config.json'  
PLANNER_PROMPT_FILE = 'planner_prompt.txt'  
COMMAND_PROMPT_FILE = 'command_validation_prompt.txt' 
RESPONSE_ENHANCEMENT_PROMPT_FILE = 'response_enhancement_prompt.txt'
AVATAR_MODE_PROMPT="avatar_mode_prompt.txt"

async def read_file_async(file_path: str) -> str:  
    """Read a file asynchronously."""  
    async with aiofiles.open(file_path, 'r') as f:  
        return await f.read()  
    
def clean_and_convert_to_dict(service_response):
    try:
        # Remove leading/trailing whitespace
        service_response = service_response.strip()
        
        # Remove any backslashes not part of an escape sequence
        service_response = re.sub(r'\\(?![nrt\\"\'b])', r'\\\\', service_response)
        
        # Replace escape sequences like \n, \t with space or appropriate character
        service_response = re.sub(r'\\n', ' ', service_response)  # Replace \n with a space
        service_response = re.sub(r'\\t', ' ', service_response)  # Replace \t with a space
        
        # Convert double backslashes to single (to address issues where backslashes are improperly escaped)
        service_response = re.sub(r'\\\\', r'\\', service_response)
        
        # Handle any remaining unescaped characters
        service_response = re.sub(r'[\x00-\x1F]+', '', service_response)
        
        # Now try to load the cleaned string into a JSON object
        response_dict = json.loads(service_response)
        
        return response_dict

    except json.JSONDecodeError as e:
        return None 
    
async def parse_response(service_response: str) -> Tuple[Any, Optional[Any], Optional[Any], Optional[Any]]:  
    """Parse the JSON response from a service."""  
    try:  
        logging.info(f"service response is : {service_response}")
        
        # Extract and clean the dictionary
        response_dict = clean_and_convert_to_dict(service_response)

        if not response_dict and 'TextResponse' not in service_response:
            return service_response, None, None

        # Extract the image link and video link from the raw service response
        text_response = response_dict['TextResponse'] if 'TextResponse' in response_dict else ''
        if not text_response:
            text_response = response_dict['QueryResponse'] if 'QueryResponse' in response_dict else ''
        response_type = response_dict['ResponseType'] if 'ResponseType' in response_dict else ''            
        image_base64 = response_dict['GraphResponse'] if 'GraphResponse' in response_dict else ''
        # Log the extracted values
        logging.info(f"text response is : {text_response}")
        logging.info(f"response type is : {response_type}")
        logging.info(f"image base64 is : {image_base64}")
        return text_response, response_type, image_base64
          
    except json.JSONDecodeError as e:  
        logging.error(f"JSON decode error: {e}")  
        return service_response, None, None 


def get_app_config() -> AppConfig:  
    """Get application configuration."""  
    return AppConfig.get_instance()  

def initialize_openai_utility(appconfig: AppConfig) -> OpenAIUtility:  
    """Initialize OpenAI utility based on application configuration."""  
    return OpenAIUtility(  
        openai_api_base=appconfig.OPENAI_API_BASE,  
        openai_api_key=appconfig.OPENAI_API_KEY,  
        openai_api_version=appconfig.OPENAI_API_VERSION,
        cosmos_endpoint=None,
        cosmos_key=None,
        cosmos_container_name=None,
        cosmos_database_name=None
    )  


async def generate_next_query_suggestion(current_question: str, current_response: str, suggestion_prompt_file_path: str, openai_utility: OpenAIUtility, request_data: RequestData, appconfig: AppConfig) -> str:  
    """Generate the next query suggestion based on the current question and response."""  
    if not appconfig.GENERATE_QUERY_SUGGESTIONS:  
        return ""  

    suggestion_prompt: str = await read_file_async(suggestion_prompt_file_path)  
    prompt = [  
        {"role": "system", "content": suggestion_prompt},  
        {"role": "user", "content": f"User Query:{current_question}'### Bot Response:{current_response}"}  
    ]  
    result = await openai_utility.generate_completion(  
        prompt=prompt, gpt_deployment_name=appconfig.GPT_4, conversation_id=request_data.RequestId  , request_id = request_data.RequestId
    )  
    return result  


async def handle_request(Invoker: SmartInvoker, request: Dict[str, Any], request_data: RequestData, status_callback, appconfig: AppConfig, suggestion_prompt_file_path: str, openai_utility: OpenAIUtility) -> func.HttpResponse:  
    """Handle the main request logic."""  
    try: 
        appconfig: AppConfig = get_app_config()   
        start_time: datetime = datetime.now(timezone.utc)  
        status_callback("Initiating query execution planning")
        response, agent_list = await Invoker.handle_request(request, status_callback)  
        end_time: datetime = datetime.now(timezone.utc)  

        duration: float = (end_time - start_time).total_seconds()  
        logdata: list = [  
            ["UserId", request_data.UserId],  
            ["UserEmail", request_data.UserEmail],  
            ["Query", request_data.Query],  
            ["Duration (Sec)", duration]  
        ]  
        log_message: str = tabulate(logdata, tablefmt="grid")  
        logging.info(f'\n{log_message}\n')  

        if request_data.IsShowPlanOnly:  
            return func.HttpResponse(response, status_code=200)  

        query_response, response_type, image_base64data  = await parse_response(response)  
        next_query_suggestion = await generate_next_query_suggestion(  
            request_data.Query, query_response, suggestion_prompt_file_path, openai_utility, request_data, appconfig  
        )  
        if agent_list and agent_list != "UserProxyAgent":
            telemterydata= f"\n ⏱ **Exec Time:** {duration:.0f} sec  |  🤖 **Agents Involved:** {agent_list}" if agent_list else f"\n \n ⏱ **Exec Time:** {duration:.0f} sec"
        else :
            telemterydata=""

        if request_data.RequestId == 'acs':
            query_response=await avatar_response(request_data.Query,query_response,openai_utility, request_data)
        else:
            query_response = await refine_response(request_data, openai_utility, query_response)
        
        
        responsejson = {  
            "Question": request_data.Query,  
            "Answer": query_response,  
            "Suggestions": next_query_suggestion  ,
            "Image": image_base64data,
            "TelemetryData":telemterydata,
            "RequestId":request_data.RequestId,
            "responseType": response_type if response_type else ""
        }  
        return func.HttpResponse(json.dumps(responsejson), status_code=200)  

    except json.JSONDecodeError as e:  
        logging.error(f'JSON decode error: {e}')  
        return func.HttpResponse("Invalid JSON format", status_code=400)  
    except KeyError as e:  
        logging.error(f'Missing key in request data: {e}')  
        return func.HttpResponse("Missing data", status_code=400)  
    except Exception as e:  
        logging.exception('Error handling request')  
        return func.HttpResponse("Oops! Something went wrong while handling your request. Please try again", status_code=500) 

async def refine_response(request_data, openai_utility, query_response):
    try:
        messages = [
        {"role": "user", "content": query_response}
        ]
        if count_tokens(messages)<1500:
            logging.info(f'origional resposne :{query_response}')
            query_response = await enhance_response(request_data.Query,query_response,openai_utility,request_data)
            logging.info(f'enhanced response:{query_response}')
        return query_response 
    except Exception as e:  
        return query_response

async def enhance_response(origional_question: str,response:str,openai_utility: OpenAIUtility,request_data: RequestData) -> str:
    try:
        app_config: AppConfig = get_app_config()
        current_dir: str = os.getcwd()  
        response_prompt_file_path: str = os.path.join(current_dir, PROMPT_LIBRARY_DIR, RESPONSE_ENHANCEMENT_PROMPT_FILE) 
        response_enhancement_prompt = await read_file_async(response_prompt_file_path)
        system_prompt = (  
            f"Current date is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"  
            f"user Id is {request_data.UserId}\n"
            f"{response_enhancement_prompt}\n"  
        ) 
        
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Query:{origional_question}'### Bot Response:{response}"}
        ]
        result = await openai_utility.generate_completion(prompt= prompt,gpt_deployment_name= app_config.GPT_DEPLOYMENT_NAME,ai_assistant=app_config.MODULE_NAME,conversation_id=request_data.RequestId, max_token=4048 , request_id = request_data.RequestId)  
        
        return result
    except Exception as e:
        logging.error(f"Error in enhancing response: {e}")
        return response
    

async def avatar_response(origional_question: str,response:str,openai_utility: OpenAIUtility,request_data: RequestData) -> str:
    try:
        app_config: AppConfig = get_app_config()
        current_dir: str = os.getcwd()  
        response_prompt_file_path: str = os.path.join(current_dir, PROMPT_LIBRARY_DIR, AVATAR_MODE_PROMPT) 
        avata_mode_prompt = await read_file_async(response_prompt_file_path)
        system_prompt = (  
            f"Current date is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"  
            f"user Id is {request_data.UserId}\n"
            f"{avata_mode_prompt}\n"  
        ) 
        
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Query:{origional_question}'### Bot Response:{response}"}
        ]
        result = await openai_utility.generate_completion(prompt= prompt,gpt_deployment_name= app_config.GPT_DEPLOYMENT_NAME,ai_assistant=app_config.MODULE_NAME,conversation_id=request_data.RequestId, request_id = request_data.RequestId)  
        
        return result
    except Exception as e:
        logging.error(f"Error in enhancing response: {e}")
        return response

async def Invoker(req: func.HttpRequest) -> func.HttpResponse:  
    """Entry point for the Invoker function."""  
    logging.info('Invoker function invoked')  

    try:  
        appconfig: AppConfig = get_app_config()  
        openai_utility = initialize_openai_utility(appconfig)  

        current_dir: str = os.getcwd()  
        suggestion_prompt_file_path: str = os.path.join(current_dir, PROMPT_LIBRARY_DIR, SUGGESTION_PROMPT_FILE)  
        config_file_path: str = os.path.join(current_dir, AGENT_LIBRARY_DIR, CONFIG_FILE)  
        planner_file_path: str = os.path.join(current_dir, PROMPT_LIBRARY_DIR, PLANNER_PROMPT_FILE)  
        command_file_path: str = os.path.join(current_dir, PROMPT_LIBRARY_DIR, COMMAND_PROMPT_FILE)  

        request: Dict[str, Any] = req.get_json()  
        request_data = RequestData(**request)  

        Invoker: SmartInvoker = await SmartInvoker.create(  
            config_path=config_file_path,  
            planner_prompt_file_path=planner_file_path,  
            request_data=request_data,  
            command_prompt_path=command_file_path,  
            openai=openai_utility
        )  

        def status_callback(status: str) -> None:  
            logging.info(f'\n********\nStatus update: {status}\n*******\n')  

        return await handle_request(Invoker, request, request_data, status_callback, appconfig, suggestion_prompt_file_path, openai_utility)  

    except json.JSONDecodeError as e:  
        logging.error(f'JSON decode error: {e}')  
        return func.HttpResponse("Invalid JSON format", status_code=400)  
    except KeyError as e:  
        logging.error(f'Missing key in request data: {e}')  
        return func.HttpResponse("Missing data", status_code=400)  
    except Exception as e:  
        logging.error(f'Error initializing Invoker: {e}')  
        return func.HttpResponse("Error initializing Invoker", status_code=500)  


async def main(req: func.HttpRequest) -> func.HttpResponse:  
    """Main entry point for the Azure Function."""  
    return await Invoker(req)  
