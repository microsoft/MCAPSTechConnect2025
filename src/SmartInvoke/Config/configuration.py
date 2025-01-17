from typing import Optional
from common.app_configuration import BaseAppConfig
  
class AppConfig(BaseAppConfig):  
    
    @property  
    def OPENAI_API_KEY(self) -> str:  
        return self.load_config_value('OPENAI_API_KEY', None) 
    
    @property  
    def OPENAI_API_BASE(self) -> str:  
        return self.load_config_value('OPENAI_API_BASE', "")  
  
    @property  
    def OPENAI_API_VERSION(self) -> str:  
        return self.load_config_value('OPENAI_API_VERSION', "")  
  
    @property  
    def GPT_DEPLOYMENT_NAME(self) -> str:  
        return self.load_config_value('GPT_DEPLOYMENT_NAME', "gpt-4o")    
    @property
    def MODULE_NAME(self) -> str:
        return self.load_config_value('MODULE_NAME', "Smart-Invoker")
    
    @property  
    def GPT_35_TURBO(self) -> str:  
        return self.load_config_value('GPT_35_TURBO', "gpt-35-turbo")  
  
    @property  
    def GPT_4_32_MODEL(self) -> str:  
        return self.load_config_value('GPT_4_32_MODEL', "gpt-4-32k")  
  
    @property  
    def GPT_4(self) -> str:  
        return self.load_config_value('GPT_4', "gpt-4o")  
  
    @property  
    def USE_CACHE(self) -> bool:  
        return self.load_bool_config_value('USE_CACHE', False)  
  
    @property  
    def USE_HISTORY(self) -> bool:  
        return self.load_bool_config_value('USE_HISTORY', True)  
  
    @property  
    def IS_PERMISSION_CHECK_ENABLED(self) -> bool:  
        return self.load_bool_config_value('IS_PERMISSION_CHECK_ENABLED', False)  
  
    @property  
    def CACHE_TYPE(self) -> str:  
        return self.load_config_value('CACHE_TYPE', "redis")  
  
    @property  
    def REDIS_HOST(self) -> str:  
        return self.load_config_value('REDIS_HOST', "")  
  
    @property  
    def REDIS_PASSWORD(self) -> str:  
        return self.load_config_value('REDIS_PASSWORD', None)   
    
    @property  
    def USER_HISTORY_RETRIEVAL_LIMIT(self) -> int:  
        return int(self.load_config_value('USER_HISTORY_RETRIEVAL_LIMIT', 10))  
  
    @property  
    def HR_INSIGHT_SERVICE_URL(self) -> str:  
        return self.load_config_value('HR_INSIGHT_SERVICE_URL', "http://localhost:9999/api/HRInsightService")  

  
    @property  
    def HR_DOCUMENT_GENERATION_SERVICE_URL(self) -> str:  
        return self.load_config_value('HR_DOCUMENT_GENERATION_SERVICE_URL', "http://localhost:5555/api/HRDocGen")  
  
    @property  
    def COSMOS_ENDPOINT(self) -> str:  
        return self.load_config_value('COSMOS_ENDPOINT', "")  
  
    @property  
    def COSMOS_DB_NAME(self) -> str:  
        return self.load_config_value('COSMOS_DB_NAME', "")  
  
    @property  
    def COSMOS_CONTAINER_NAME(self) -> str:  
        return self.load_config_value('COSMOS-ANALYTICS-CONTAINER-NAME', "")   
  
    @property
    def AZURE_TENANT_ID(self) -> str:
        return self.load_config_value('AZURE_TENANT_ID', "")
    
    @property
    def USER_PROFILE_CLIENT_ID(self) -> str:
        return self.load_config_value('USER_PROFILE_CLIENT_ID', "")
    
    @property
    def USER_PROFILE_CLIENT_SECRET(self) -> str:
        return self.load_config_value('USER_PROFILE_CLIENT_SECRET', "")
    
    @property
    def INCLUDE_USER_PROFILE(self) -> bool:
        return self.load_bool_config_value('INCLUDE_USER_PROFILE', False)
    
    @property
    def GENERATE_QUERY_SUGGESTIONS(self) -> bool:
        return self.load_bool_config_value('GENERATE_QUERY_SUGGESTIONS', True)
    
    @property
    def PROCESS_COMMANDS(self) -> bool:
        return self.load_bool_config_value('PROCESS_COMMANDS', True)

    @property  
    def TENANT_ID(self) -> str:  
        return self.load_config_value('TENANT_ID', "")

    @property  
    def TENANT_CLIENTID(self) -> str:  
        return self.load_config_value('TENANT_CLIENTID', "")   