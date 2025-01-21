import json
import os
import logging
import timeit
import hashlib
import inspect
import tiktoken
import requests
import re
import aiohttp

from azure.identity import ClientSecretCredential

DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

def log_execution_time(func):
    """
    A decorator that logs the duration of method execution.

    Args:
    func (callable): The function to be decorated.

    Returns:
    The decorated function.
    """
    def wrapper(*args, **kwargs):
        input_str = f"Input: {args}, {kwargs}"
        if DEBUG_MODE:
            logging.info(f"Executing {func.__name__} with {input_str}")
        start_time = timeit.default_timer()
        result = func(*args, **kwargs)
        end_time = timeit.default_timer()
        duration = end_time - start_time
        if DEBUG_MODE:
            logging.info(f"{func.__name__} took {duration} seconds to execute.")
        return result

    return wrapper

def track_execution_time(cls):
    for name, method in inspect.getmembers(cls, predicate=inspect.ismethod):
        setattr(cls, name, log_execution_time(method))
    return cls

def generate_cache_key(user_id, user_query, is_permission_check_enabled):
    query_text = f'{user_id}_{user_query}' if is_permission_check_enabled else f'{user_query}'
    hash_object = hashlib.sha256()
    hash_object.update(query_text.encode('utf-8'))
    hash_value = hash_object.hexdigest()
    return hash_value


def split_text_by_token(text: str, max_tokens: int, chunk_overlap: int) -> list:  
    """Split a text into chunks of a maximum number of tokens with a specified overlap."""
    if max_tokens <= 0:  
        raise ValueError("max_tokens must be greater than 0")  
    if chunk_overlap < 0:  
        raise ValueError("chunk_overlap must be non-negative")  
    if chunk_overlap >= max_tokens:  
        raise ValueError("chunk_overlap must be less than max_tokens")  

    tokenizer = tiktoken.encoding_for_model("gpt-4-0314")  
    tokens = tokenizer.encode(text)  

    if not tokens:  
        return []  

    chunks = []  
    start = 0  
    while start < len(tokens):  
        end = start + max_tokens  
        chunk = tokens[start:end]  
        chunks.append(chunk)  
        start += max_tokens - chunk_overlap  

    text_chunks = [tokenizer.decode(chunk) for chunk in chunks]  
    return text_chunks 

def count_tokens_str(messages, model="gpt-3.5-turbo-0613")->int:
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(messages))
    except KeyError:
        logging.info("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(messages))
        
def count_tokens(messages, model="gpt-3.5-turbo-0613"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logging.info("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        
        return count_tokens(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        
        return count_tokens(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

def get_arm_access_token(tenant_id, client_id, client_secret) -> str:
    credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    scope = "https://management.azure.com/.default" 
    token = credential.get_token(scope)
    return token.token

def extract_account_url(auth_url)-> str:
    # Extract SubscriptionId, ResourceGroup, and AccountName from the authentication URL using regular expressions
    match = re.search(r'subscriptions/([^/]+)/resourceGroups/([^/]+)/providers/Microsoft.VideoIndexer/accounts/([^/]+)', auth_url)
    if match:
        subscription_id = match.group(1)
        resource_group = match.group(2)
        account_name = match.group(3)
        # Construct the account URL
        account_url = f'https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.VideoIndexer/accounts/{account_name}?api-version=2024-01-01'
        return account_url
    else:
        raise ValueError("Invalid authentication URL format") 

def get_account_async(account_url,arm_access_token) -> dict:
               
        headers = {
            'Authorization': 'Bearer ' + arm_access_token,
            'Content-Type': 'application/json'
        }
            
        response = requests.get(account_url, headers=headers)
        response.raise_for_status()
        return response.json()
           
def get_account_access_token_async(url, params, arm_access_token, video_id=None)-> str:
    
    headers = {
        'Authorization': 'Bearer ' + arm_access_token,
        'Content-Type': 'application/json'
    }

    if video_id is not None:
        params['videoId'] = video_id

    response = requests.post(url, json=params, headers=headers)
    
    # check if the response is valid
    response.raise_for_status()
    access_token = response.json().get('accessToken')
    return access_token

async def post_request(url: str, params: dict) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            return data
        
async def async_get(url: str, params: dict = None) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                raise Exception(f"Failed to get response from service. : {response.reason}")
            return await response.json()

async def async_get_service_response(url:str,data:str, access_token=None)-> str:
    if access_token is not None:
       headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    else:
        headers = {'Content-Type': 'application/json'} 
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers,  data=data) as response:
            if response.status != 200 and response.status != 201 and response.status != 500:
                raise Exception(f"Failed to get response from service. : {response.reason}")
            return await response.text()

def parse_responsejson(result):
        try:
            # Remove the leading 'json\n' if present
            result = result.replace('json\n', '')

            # Find the start and end indices of the JSON object
            json_start_index = result.find('{')
            json_end_index = result.rfind('}')  # Using rfind to ensure we get the last closing brace

            # Extract and trim the JSON object from the result
            json_string = result[json_start_index:json_end_index + 1].strip()

            response_body = json.loads(json_string)
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {str(e)}")
            
            # Attempt to fix the string by replacing backslashes
            fixed_result = result.replace('\\', '\\\\')

            try:
                response_body = json.loads(fixed_result)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse fixed JSON string: {str(e)}")
                response_body = None
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            response_body = None

        return response_body

