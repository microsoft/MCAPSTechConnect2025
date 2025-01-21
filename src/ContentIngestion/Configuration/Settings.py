import logging
import os
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic import BaseModel
from Models.DataSources import DataSources
from Utilities.Exceptions import *

class Settings(BaseModel):
    openai_api_type: Optional[str] = ""
    openai_api_base: Optional[str] = ""
    openai_api_version: Optional[str] = ""
    vector_index_engine: Optional[str] = "AzureCognitiveSearch"
    azure_cognitive_search_service_Name: Optional[str] = ""
    azure_cognitive_search_service_url: Optional[str] = ""
    azure_cognitive_admin_key:Optional[str] = ""
    azure_cognitive_search_index_name: Optional[str] = "techconnectdemoindex"
    chunk_size : Optional[int] = 1024
    use_cache : Optional[bool]=True
    cache_type : Optional[str]="redis"
    redis_host : Optional[str]=""
    user_history_retrieval_limit : Optional[int]=10
    blob_sas_url_expiry_window : Optional[int]= 60
    is_parse_by_docintelligence:Optional[bool]=False
    
    def __init__(self):
        super().__init__()
        self.load_config()

    def fetch_secret_value(self, secret_client: SecretClient, env_key, default_value=None):
        try:
            val = os.environ.get(env_key)
            
            if val is None or val == '':
                kv_key = env_key.replace('_', '-')
                try:
                    val = secret_client.get_secret(kv_key).value
                except Exception as e:
                    logging.warning(f'Value not found for key: {kv_key}')

                if val is None or val == '':
                    if default_value is None:
                        raise ConfigurationLoadException(f'Value not found for key: {kv_key}. No default value provided.')
                    val = default_value

            if val is not None:
                os.environ[env_key] = val
            return val
        
        except Exception as e:
            logging.error(f'Error fetching secret value for key: {env_key}')
            raise ConfigurationLoadException(f'Error loading fetch_secret_value: {e}') 
          
    def load_config(self):
        try:
            logging.info('Loading configuration from Key Vault')
            credential = DefaultAzureCredential()
            secret_client = SecretClient(
            vault_url=os.environ.get("AZURE_KEY_VAULT_URL"),
                        credential=credential
                        )
            
            os.environ["VECTOR_INDEX_ENGINE"] = self.vector_index_engine
            
            if (self.vector_index_engine == "AzureCognitiveSearch"):
                self.azure_cognitive_search_service_Name = self.fetch_secret_value(secret_client,"AZURE_COGNITIVE_SEARCH_SERVICE_NAME") 
                self.azure_cognitive_search_service_url = self.fetch_secret_value(secret_client,"AZURE_COGNITIVE_SEARCH_SERVICE_URL") 
                self.azure_cognitive_search_index_name = self.fetch_secret_value(secret_client,"AZURE_COGNITIVE_SEARCH_INDEX_NAME")
                self.azure_cognitive_admin_key=self.fetch_secret_value(secret_client,"AZURE_COGNITIVE_ADMIN_KEY")
            self.openai_api_type = self.fetch_secret_value(secret_client,"OpenAI_API_Type")
            self.openai_api_base = self.fetch_secret_value(secret_client,"OPENAI_API_BASE")
            self.openai_api_version = self.fetch_secret_value(secret_client,"OPENAI_API_VERSION")
            self.is_parse_by_docintelligence = self.fetch_secret_value(secret_client,"IS_PARSE_BY_DOCINTELLIGENCE")
            
            if self.use_cache:
                self.redis_host = self.fetch_secret_value(secret_client,"REDIS_HOST")
        except Exception as e:
            logging.error(f'Error loading configuration:{e}')
            raise ConfigurationLoadException(f'Error loading configuration:{e}')
        
    def get_searchindexname(self, document_type):
        match(document_type):
            case "techconnect":
                return self.azure_cognitive_search_index_name
            case _:
                raise QueryTypeInvalidOrNotSupported("Document Type is not valid")
