from datetime import datetime, timezone
import os
from typing import Optional
import openai
from tabulate import tabulate
from pydantic import BaseModel, Field
from askai_core.common import LLMModelConfiguration
from askai_core.telemetry import OpenAiTelemetry
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential, wait_random_exponential
import logging
from openai import APIConnectionError, AsyncAzureOpenAI, AzureOpenAI
from askai_core.Utility.prompts import QUERY_SUGGESTION_PROMPT
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


class OpenAIUtility():
    DEFAULT_TEMPERATURE = 0
    DEFAULT_MAX_TOKENS = 1024
    DEFAULT_TOP_P = 0.2
    DEFAULT_MODEL_NAME = LLMModelConfiguration.get_instance()._GPT_4O
    DEFAULT_EMBEDDING_MODEL = LLMModelConfiguration.get_instance().EMEDDING_MODEL
    SCOPE = "https://cognitiveservices.azure.com/.default"

    class ConfigSchema(BaseModel):
        openai_api_base: Optional[str] = Field(..., title="OpenAI API Base")
        openai_api_key: Optional[str] = Field(..., title="OpenAI API Key")
        openai_api_version: Optional[str] = Field(..., title="OpenAI API Version")
        cosmos_endpoint: Optional[str] = Field("", title="Cosmos Endpoint")
        cosmos_key: Optional[str] = Field("", title="Cosmos Key")
        cosmos_database_name: Optional[str] = Field("", title="Cosmos Database Name")
        cosmos_container_name: Optional[str] = Field("", title="Cosmos Container Name")


    def __init__( self, 
                    openai_api_base: Optional[str] = None, 
                    openai_api_key: Optional[str] = None,
                    openai_api_version: Optional[str] = None,
                    cosmos_endpoint: Optional[str] = None,
                    cosmos_key: Optional[str] = None,
                    cosmos_database_name: Optional[str] = None,
                    cosmos_container_name: Optional[str] = None
    ):
        self.openai_api_base = openai_api_base or os.getenv('OPENAI_API_BASE')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.openai_api_version = openai_api_version or os.getenv('OPENAI_API_VERSION')
        self.cosmos_endpoint = cosmos_endpoint or os.getenv('COSMOS_ENDPOINT', "")
        self.cosmos_key = cosmos_key or os.getenv('COSMOS_KEY', "")
        self.cosmos_database_name = cosmos_database_name or os.getenv('COSMOS_DATABASE_NAME', "")
        self.cosmos_container_name = cosmos_container_name or os.getenv('COSMOS_CONTAINER_NAME', "")
        self.openai_client = self.initialize_openai_client(openai_api_base, openai_api_key, openai_api_version)
        self.openai_client_sync = self.initialize_openai_client_sync(openai_api_base, openai_api_key, openai_api_version)
        self.openai_telemetry = OpenAiTelemetry(cosmos_endpoint, cosmos_key, cosmos_database_name, cosmos_container_name)
        

    def initialize_openai_client(self,openai_api_base,openai_api_key,openai_api_version):
        if openai_api_key is None or openai_api_key == "":
            token_provider = get_bearer_token_provider(DefaultAzureCredential(), self.SCOPE)
            return AsyncAzureOpenAI(
                azure_endpoint=openai_api_base,
                api_version=openai_api_version,
                azure_ad_token_provider=token_provider
           )
        else:
            return AsyncAzureOpenAI(
                azure_endpoint=openai_api_base,
                api_key=openai_api_key,
                api_version=openai_api_version
            )

    def initialize_openai_client_sync(self,openai_api_base,openai_api_key,openai_api_version):
         if openai_api_key is None or openai_api_key == "":
            token_provider = get_bearer_token_provider(DefaultAzureCredential(), self.SCOPE)
            return AzureOpenAI(
                azure_endpoint=openai_api_base,
                api_version=openai_api_version,
                azure_ad_token_provider=token_provider
           )
         else:
           return AzureOpenAI(
                azure_endpoint=openai_api_base,
                api_key=openai_api_key,
                api_version=openai_api_version
            )
    
    @retry(  
        wait=wait_exponential(multiplier=1, min=2, max=4),  
        stop=stop_after_attempt(2),  
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError,openai.APIConnectionError))  
    )
    async def generate_completion(self, prompt, gpt_deployment_name=DEFAULT_MODEL_NAME, max_token=DEFAULT_MAX_TOKENS, ai_assistant="", conversation_id=""):
        start_time = datetime.now() 
        response = await self.openai_client.chat.completions.create(
            model=gpt_deployment_name,
            messages=prompt,
            temperature=self.DEFAULT_TEMPERATURE,
            max_tokens=max_token,
            top_p=self.DEFAULT_TOP_P
        )
        end_time =  datetime.now()
        duration = end_time - start_time

        log_message = self.generate_log_message(response, duration)  
            
                
        logging.info(f'\n{log_message}\n')
        result = response.choices[0].message.content
        model = response.model
        if self.cosmos_endpoint and self.cosmos_endpoint != " ":
          await self.openai_telemetry.capture_telemetry_data(ai_assistant, conversation_id, prompt, result, start_time, end_time, model, response.usage.completion_tokens)
        return result
    
    async def generate_completion_json_format(self, prompt, gpt_deployment_name=DEFAULT_MODEL_NAME, max_token=DEFAULT_MAX_TOKENS, ai_assistant="", conversation_id=""):
        start_time = datetime.now() 
        response = await self.openai_client.chat.completions.create(
            model=gpt_deployment_name,
            messages=prompt,
            response_format={ "type": "json_object" },
            temperature=self.DEFAULT_TEMPERATURE,
            max_tokens=max_token,
            top_p=self.DEFAULT_TOP_P
        )
        end_time =  datetime.now()
        duration = end_time - start_time

        log_message = self.generate_log_message(response, duration)  
            
                
        logging.info(f'\n{log_message}\n')
        result = response.choices[0].message.content
        model = response.model
        if self.cosmos_endpoint and self.cosmos_endpoint != " ":
          await self.openai_telemetry.capture_telemetry_data(ai_assistant, conversation_id, prompt, result, start_time, end_time, model, response.usage.completion_tokens)
        return result

    def generate_log_message(self, response, duration):
        try:
            model = response.model
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            duration_sec = duration.total_seconds()
            data = [  
                    ["Model", model],  
                    ["Prompt Tokens Used", prompt_tokens],  
                    ["Completion Tokens Generated", completion_tokens],
                    ["Duration (Sec)", duration_sec]
                ]  
                
                # Generate the tabular message  
            log_message = tabulate(data, tablefmt="grid")
            return log_message
        except Exception as e:
            logging.error(f'Error in generate_log_message: {e}')
            return ""
            

    @retry(wait=wait_exponential(multiplier=1, min=2, max=4), stop=stop_after_attempt(2))
    def generate_completion_sync(self, prompt, gpt_deployment_name= DEFAULT_MODEL_NAME, max_token=DEFAULT_MAX_TOKENS):
        start_time=datetime.now()
        response = self.openai_client_sync.chat.completions.create(
            model=gpt_deployment_name,
            messages=prompt,
            temperature=self.DEFAULT_TEMPERATURE,
            max_tokens=max_token,
            top_p=self.DEFAULT_TOP_P
        )
        end_time =  datetime.now()
        duration = end_time - start_time
        log_message = self.generate_log_message(response, duration)
        logging.info(log_message)
        result = response.choices[0].message.content
        return result

    @retry(wait=wait_exponential(multiplier=1, min=2, max=4), stop=stop_after_attempt(2))
    async def generate_nonchatcompletion(self, prompt):
        response = await self.openai_client.completions.create(
            model=self.settings.GPT_35_TURBO,
            prompt=prompt,
            temperature=self.DEFAULT_TEMPERATURE,
            max_tokens=self.DEFAULT_MAX_TOKENS,
            top_p=self.DEFAULT_TOP_P,
            stop=[""]
        )
        result = response.choices[0].text
        return result

    

    @retry(wait=wait_exponential(multiplier=1, min=2, max=4), stop=stop_after_attempt(2))
    async def get_query_suggestions(self, question: str, response: str, gpt_deployment_name: str = DEFAULT_MODEL_NAME, ai_assistant="", conversation_id=""):
        try:
            prompt = [
                {"role": "system", "content": QUERY_SUGGESTION_PROMPT},
                {"role": "user", "content": f"User Query:{question}'### Bot Response:{response}"}
            ]
            result = await self.generate_completion(prompt, gpt_deployment_name, 200, ai_assistant, conversation_id)
            return result
        except Exception as e:
            logging.error(str(e))
            raise APIConnectionError("Unable to connect to OpenAI")

    async def get_avatar_response(self, user_query: str, original_response: str, userid: str,  gpt_deployment_name: str = LLMModelConfiguration.get_instance().GPT_4, ai_assistant="", conversation_id=""):
        try:
            prompt = [
                {"role": "system", "content": f"Imagine you got the below response from the backend bot for user question ('{user_query}') and you need to reframe the original response to make it super easy and interesting for the audience who are procurement professionals. Pretend you're a top-notch speaker speaking to a senior business professional who has asked you for this information, making sure the content is a breeze for him to grasp while keeping the tone professional. Keep all the facts spot on, no need to assume he knows it all already. Maintain the accuracy of the details provided in the original text. Also never start with Ladies and Gentlemen, and always begin with thanking the user for asking question. do not include any new lines or markdown characters in the response and also ensure that the content is concise and can be delivered verbally within a 1-minute timeframe ' "},
                {"role": "user", "content": f"original response:{original_response}"}
            ]
            result = self.generate_completion(prompt, gpt_deployment_name, 1048, ai_assistant, conversation_id)
            return result
        except Exception as e:
            logging.error(str(e))
            raise APIConnectionError("Unable to connect to OpenAI")


    @retry(wait=wait_exponential(multiplier=1, min=2, max=4), stop=stop_after_attempt(2))
    def generate_image_description(self, image_url, text_data, prompt, gpt_deployment_name:str = DEFAULT_MODEL_NAME):
        try:
            prompt =[
                { "role": "system", "content": prompt },
                { "role": "user", "content": [  
                    { 
                        "type": "text", 
                        "text": text_data 
                    },
                    { 
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]} 
            ]
            result = self.generate_completion_sync(prompt, gpt_deployment_name, int(LLMModelConfiguration.get_instance().MAX_TOKEN_COUNT))
            return result
        except RetryError as retry_error:
            last_exception = retry_error.last_attempt.exception()
            if last_exception is not None:
                policy_violation_message = retry_error.last_attempt.exception().message
                logging.error(policy_violation_message)
            else:
                print("RetryError occurred:", retry_error)
        except Exception as e:
            logging.error(str(e))
            raise APIConnectionError("Unable to connect to OpenAI")
    
    @retry(wait=wait_exponential(multiplier=1, min=2, max=4), stop=stop_after_attempt(2))  
    async def get_generic_reponse(self, question):
        try:
            response = await self.openaiclient.chat.completions.create(
                model=LLMModelConfiguration.get_instance().GPT_4, 
                messages=question,
                temperature=self.DEFAULT_TEMPERATURE,
                max_tokens=self.DEFAULT_MAX_TOKENS,
                top_p=self.DEFAULT_TOP_P
            )
            result = response.choices[0].message.content          
            return result
        except Exception as e:
            logging.error(str(e))
            raise APIConnectionError("Unable to connect to OpenAI")
        
    def convert_to_utc_iso(self, dt):
        # Convert it to UTC
        dt = dt.astimezone(timezone.utc)
        # Convert it to ISO 8601 format
        iso_format = dt.isoformat()
        return iso_format
    
    def generate_embeddings(self, text, model_name=DEFAULT_EMBEDDING_MODEL):
        return self.openai_client_sync.embeddings.create(
            input=text, model=model_name).data[0].embedding
    
    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    async def generate_embeddings_async(self, text, model_name=DEFAULT_EMBEDDING_MODEL):
        response = await self.openai_client.embeddings.create(input=text, model=model_name)
        embeddings = response.data[0].embedding
        return embeddings