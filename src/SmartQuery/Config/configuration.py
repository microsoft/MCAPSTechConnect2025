import logging  
import os  
from typing import Optional, Dict, Any  
from azure.identity import DefaultAzureCredential  
from azure.keyvault.secrets import SecretClient  
  
from distutils.util import strtobool  
  
class AppConfig():  
    _instance: Optional['AppConfig'] = None  
    _config_cache: Dict[str, Any] = {}  
    _secret_client: Optional[SecretClient] = None  
  
    class Config:  
        env_file = ".env"  
  
    def __new__(cls, **data):  
        if cls._instance is None:  
            cls._instance = super(AppConfig, cls).__new__(cls)  
            cls._instance.__initialized = False  
        return cls._instance  
  
    def __init__(self, **data):  
        if getattr(self, '__initialized', False):  
            return  
        super().__init__(**data)  
  
    @classmethod  
    def get_instance(cls) -> 'AppConfig':  
        if cls._instance is None:  
            cls._instance = AppConfig()  
        return cls._instance  
  
    @classmethod  
    def get_secret_client(cls) -> SecretClient:  
        if cls._secret_client is None:  
            credential = DefaultAzureCredential()  
            cls._secret_client = SecretClient(vault_url=os.getenv("AZURE_KEY_VAULT_URL"), credential=credential)  
        return cls._secret_client  
    
    def fetch_secret_value_from_keyvault(self, key:str) -> str:  
        try:  
            secret =  self.get_secret_client().get_secret(key)
            return secret.value  
        except Exception as e:  
            logging.error(f'Error fetching secret value for key: {key}: {e}')  
            return ""
    
    def fetch_secret_value(self, secret_client: SecretClient, env_key: str, default_value: Optional[str] = None) -> str:  
        try:  
            val = os.getenv(env_key)  
            if not val:  
                kv_key = env_key.replace('_', '-')
                try:  
                    val = secret_client.get_secret(kv_key).value  
                except Exception:  
                    logging.warning(f'Value not found for key: {kv_key}')  
                if not val and default_value is not None:  
                    val = default_value  
                elif not val:  
                    raise ValueError(f'Value not found for key: {kv_key}. No default value provided.')  
            os.environ[env_key] = val  
            return val  
        except Exception as e:  
            logging.error(f'Error fetching secret value for key: {env_key}: {e}')  
            return "" 
  
    def load_config_value(self, key: str, default_value: Optional[str] = None) -> Any:  
        if key in self._config_cache:  
            return self._config_cache[key]
  
        secret_client = self.get_secret_client()  
        value = self.fetch_secret_value(secret_client, key.upper(), default_value)  
        if value != "":  
            self._config_cache[key] = value  
        return value  
  
    def load_bool_config_value(self, key: str, default_value: bool) -> bool:  
        value = self.load_config_value(key, str(default_value))  
        return bool(strtobool(value)) if isinstance(value, str) else bool(value) 
  
    @property  
    def openai_api_key(self) -> str:  
        return self.load_config_value('OPENAI_API_KEY', "")  
  
    @property  
    def openai_api_base(self) -> str:  
        return self.load_config_value('OPENAI_API_BASE', "")  
  
    @property  
    def openai_api_version(self) -> str:  
        return self.load_config_value('OPENAI_API_VERSION', "") 
    
    @property  
    def openai_gpt_deployment_name(self) -> str:  
        return self.load_config_value('GPT_DEPLOYMENT_NAME', "") 
    
    @property  
    def openai_embedding_deployment_name(self) -> str:  
        return self.load_config_value('EMBEDDING_DEPLOYMENT_NAME', "")  
  
    @property  
    def use_cache(self) -> bool:  
        return self.load_bool_config_value('USE_CACHE', True)  
  
    @property  
    def is_permission_check_enabled(self) -> bool:  
        return self.load_bool_config_value('IS_PERMISSION_CHECK_ENABLED', False) 
    
    @property
    def module_name(self) -> str:
        return self.load_config_value('MODULE_NAME', "Product-Insight")
  
    @property  
    def cache_type(self) -> str:  
        return self.load_config_value('CACHE_TYPE', "redis")  
  
    @property  
    def redis_host(self) -> str:  
        return self.load_config_value('REDIS_HOST', "")  
  
    @property  
    def redis_password(self) -> str:  
        return self.load_config_value('REDIS_PASSWORD', "")
  
    @property  
    def azure_cognitive_admin_key(self) -> str:  
        return self.load_config_value('AZURE_COGNITIVE_ADMIN_KEY_1', "")
  
    @property  
    def azure_cognitive_search_automotive_index_name(self) -> str:  
        return self.load_config_value('AZURE_COGNITIVE_SEARCH_AUTOMOTIVE_INDEX_NAME', "")  
  
    @property  
    def azure_cognitive_search_service_url(self) -> str:  
        return self.load_config_value('AZURE_COGNITIVE_SEARCH_SERVICE_URL', "")  
    
    @property  
    def askai_cosmos_db_endpoint(self) -> str:  
        return self.load_config_value('COSMOS_ENDPOINT', "")  
    
    @property  
    def askai_cosmos_db_name(self) -> str:  
        return self.load_config_value('COSMOS_DATABASE_NAME', "")  
    
    @property  
    def askai_analytics_cosmos_db_container(self) -> str:  
        return self.load_config_value('COSMOS_ANALYTICS_CONTAINER_NAME', "")
    
    @property  
    def apim_gateway_url(self) -> str:  
        return self.load_config_value('APIM_GATEWAY_URL', "")  

    @property  
    def apim_subscription_key(self) -> str:  
        return self.load_config_value('APIM_SUBSCRIPTION_KEY', "")   