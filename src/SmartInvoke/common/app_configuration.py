import logging  
import os  
from typing import Optional, Dict, Any, Type  
from azure.identity import DefaultAzureCredential  
from azure.keyvault.secrets import SecretClient  
from distutils.util import strtobool  
  
class BaseAppConfig:  
    _instances: Dict[Type['BaseAppConfig'], 'BaseAppConfig'] = {}  
    _config_cache: Dict[str, Any] = {}  
    _secret_client: Optional[SecretClient] = None  
  
    class Config:  
        env_file = ".env"  
  
    def __new__(cls, **data: Any) -> 'BaseAppConfig':  
        if cls not in cls._instances:  
            instance = super(BaseAppConfig, cls).__new__(cls)  
            instance.__initialized = False  
            cls._instances[cls] = instance  
        return cls._instances[cls]  
  
    def __init__(self, **data: Any):  
        if getattr(self, '__initialized', False):  
            return  
        super().__init__(**data)  
        self.__initialized = True  
  
    @classmethod  
    def get_instance(cls) -> 'BaseAppConfig':  
        return cls(**{})  
  
    @classmethod  
    def get_secret_client(cls) -> SecretClient:  
        if cls._secret_client is None:  
            credential = DefaultAzureCredential()  
            cls._secret_client = SecretClient(vault_url=os.getenv("AZURE_KEY_VAULT_URL"), credential=credential)  
        return cls._secret_client  
  
    def fetch_secret_value_from_keyvault(self, key: str) -> Optional[str]:  
        try:  
            secret = self.get_secret_client().get_secret(key)  
            return secret.value  
        except Exception as e:  
            logging.error(f'Error fetching secret value for key: {key}: {e}')  
            return None  
  
    def fetch_secret_value(self, secret_client: SecretClient, env_key: str, default_value: Optional[str] = None) -> Optional[str]:  
        try:  
            val = os.getenv(env_key)  
            if not val:  
                kv_key = env_key.replace('_', '-')  
                try:  
                    val = secret_client.get_secret(kv_key).value  
                except Exception as e:  
                    logging.warning(f'Value not found for key: {kv_key}. Error: {e}')  
                if not val :  
                    val = default_value  
            if val:    
                os.environ[env_key] = val  
            return val  
        except Exception as e:  
            logging.error(f'Error fetching secret value for key: {env_key}: {e}')  
            return None  
  
    def load_config_value(self, key: str, default_value: Optional[str] = None) -> Optional[Any]:  
        if key in self._config_cache:  
            return self._config_cache[key]  
  
        secret_client = self.get_secret_client()  
        value = self.fetch_secret_value(secret_client, key.upper(), default_value)  
        if value is not None:  
            self._config_cache[key] = value  
        return value  
  
    def load_bool_config_value(self, key: str, default_value: bool) -> bool:  
        value = self.load_config_value(key, str(default_value))  
        return bool(strtobool(value)) if isinstance(value, str) else bool(value)  
 