import os  
from typing import Optional  
  
class LLMModelConfiguration:  
    """  
    This class contains all the constants used in the project.  
    Values are read from environment variables if available, otherwise defaults are used.  
    """  
    _instance = None  
  
    _OPENAI_API_VERSION: Optional[str] = os.getenv("OPENAI_API_VERSION", "2023-05-15")  
    _GPT_35_TURBO: Optional[str] = os.getenv("GPT_35_TURBO", "gpt-35-turbo")  
    _GPT_4_32_MODEL: Optional[str] = os.getenv("GPT_4_32_MODEL", 'gpt-4-32k')  
    _GPT_4: Optional[str] = os.getenv("GPT_4", "gpt-4o")
    _GPT_4O: Optional[str] = os.getenv("GPT_4O", "gpt-4o")
    _GPT_4_VISION: Optional[str] = os.getenv("GPT_4_VISION", "gpt-4o")  
    _EMEDDING_MODEL: Optional[str] = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")  
    _MAX_TOKEN_COUNT: Optional[str] = os.getenv("MAX_TOKEN_COUNT", "250")  
  
    def __new__(cls, *args, **kwargs):  
        if cls._instance is None:  
            cls._instance = super().__new__(cls, *args, **kwargs)  
        return cls._instance  
  
    @classmethod  
    def get_instance(cls):  
        if cls._instance is None:  
            cls._instance = cls()  
        return cls._instance  
  
    @property  
    def max(self) -> str:  
        return self._OPENAI_API_VERSION  
    
    @property  
    def MAX_TOKEN_COUNT(self) -> str:  
        return self._MAX_TOKEN_COUNT 
    
    @property  
    def OPENAI_API_VERSION(self) -> str:  
        return self._OPENAI_API_VERSION  
  
    @property  
    def GPT_35_TURBO(self) -> str:  
        return self._GPT_35_TURBO  
  
    @property  
    def GPT_4_32_MODEL(self) -> str:  
        return self._GPT_4_32_MODEL  
  
    @property  
    def GPT_4(self) -> str:  
        return self._GPT_4  
  
    @property  
    def GPT_4_VISION(self) -> str:  
        return self._GPT_4_VISION  
  
    @property  
    def EMEDDING_MODEL(self) -> str:  
        return self._EMEDDING_MODEL  
