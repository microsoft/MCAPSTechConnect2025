from enum import Enum  
import logging  
import os
import base64
import json
import redis  
import pickle
import time
from azure.identity import DefaultAzureCredential
  
USE_CACHE = os.getenv("USE_CACHE", "True").lower() == "true"  

scope = "https://redis.azure.com/.default"
  
class BaseCacheWrapper:  
    def rpush(self, user_key, json_data):  
        raise NotImplementedError("rpush method must be implemented in the derived class.")  
      
    def lrange(self, user_key, start, end):  
        raise NotImplementedError("lrange method must be implemented in the derived class.")  
      
    def read_from_cache(self, key):  
        raise NotImplementedError("read_from_cache method must be implemented in the derived class.")  
      
    def write_to_cache(self, key, value, expiration_time=None):  
        raise NotImplementedError("write_to_cache method must be implemented in the derived class.")  
      
    def read_object_from_cache(self, key):  
        raise NotImplementedError("read_object_from_cache method must be implemented in the derived class.")  
      
    def write_object_to_cache(self, key, value, expiration_time=None):  
        raise NotImplementedError("write_object_to_cache method must be implemented in the derived class.")  
  
class RedisCacheWrapper(BaseCacheWrapper):  
    def __init__(self, redis_host, redis_password, use_ssl=True):  
        self.redis_client = self.Authenticate(redis_host, redis_password, use_ssl) 

    def Authenticate(self, redis_host, redis_password, use_ssl):
        if redis_password == None or redis_password == "":
            cred = DefaultAzureCredential()
            token = cred.get_token(scope)
            user_name = self.extract_username_from_token(token.token)
            redisClient = redis.StrictRedis(  
                host=redis_host,  
                port=6380,  
                username=user_name,
                password=token.token,
                decode_responses=True, 
                ssl=use_ssl  
            )

            max_retry=5
            for index in range(max_retry):
                try:
                    if self._need_refreshing(token):
                        logging.info("Refreshing token...")
                        tmp_token = cred.get_token(scope)
                        if tmp_token:
                            token = tmp_token
                        redisClient.execute_command("AUTH", user_name, token.token)
                    break
                except redis.ConnectionError:
                    logging.info("Connection lost. Reconnecting.")
                    token = cred.get_token(scope)
                    redisClient = redis.StrictRedis(  
                                host=redis_host,  
                                port=6380,  
                                username=user_name,
                                password=token.token,
                                decode_responses=True, 
                                ssl=use_ssl  
                            )
                except Exception:
                    logging.info("Unknown failures.")
                    break
            return redisClient
        else:
            return redis.StrictRedis(  
                host=redis_host,  
                port=6380,  
                password=redis_password,  
                ssl=use_ssl,
                decode_responses=True
            ) 
        
    def extract_username_from_token(self, token):
        parts = token.split('.')
        base64_str = parts[1]

        if len(base64_str) % 4 == 2:
            base64_str += "=="
        elif len(base64_str) % 4 == 3:
            base64_str += "="

        json_bytes = base64.b64decode(base64_str)
        json_str = json_bytes.decode('utf-8')
        jwt = json.loads(json_str)

        return jwt['oid']
    
    def _need_refreshing(self, token, refresh_offset=300):
        return not token or token.expires_on - time.time() < refresh_offset
      
    def __enter__(self):  
        # Perform any setup if needed  
        return self  
      
    def __exit__(self, exc_type, exc_val, exc_tb):  
        # Perform any cleanup if needed  
        pass
      
    def rpush(self, user_key, json_data):  
        if USE_CACHE:  
            self.redis_client.rpush(user_key, json_data)  
      
    def lrange(self, user_key, start, end):  
        if USE_CACHE:  
            return self.redis_client.lrange(user_key, start, end)  
      
    def delete(self, user_key):  
        if USE_CACHE:  
            self.redis_client.delete(user_key)  
      
    def read_from_cache(self, key):  
        if USE_CACHE:  
            cached_value = self.redis_client.get(key)
            return cached_value 
        else:  
            return None
        
    def readstr_from_cache(self, key):  
        if USE_CACHE:  
            cached_value = self.redis_client.get(key)  
            return cached_value if cached_value else None  
        else:  
            return None  
      
    def write_to_cache(self, key, value, expiration_time=None):  
        try:  
            if USE_CACHE:  
                if expiration_time:  
                    self.redis_client.setex(key, expiration_time, value)  
                    logging.info(f"Writing to cache with expiration time: {expiration_time}")  
                else:  
                    self.redis_client.set(key, value)  
        except Exception as e:  
            logging.error(f"Error writing to cache: {e}")  
      
    def read_object_from_cache(self, key):  
        if USE_CACHE:  
            cached_value = self.redis_client.get(key)  
            return pickle.loads(cached_value) if cached_value else None  
        else:  
            return None  
      
    def write_object_to_cache(self, key, value, expiration_time=None):  
        try:  
            if USE_CACHE:  
                if expiration_time:  
                    self.redis_client.setex(key, expiration_time, pickle.dumps(value))  
                else:  
                    self.redis_client.set(key, pickle.dumps(value))  
        except Exception as e:  
            logging.error(f"Error writing to cache: {e}")  
  
class CacheType(Enum):  
    REDIS = 'redis'  
  
class CacheFactory:  
    @staticmethod  
    def get_cache(cachetype: CacheType, redis_host, redis_password):  
        if cachetype == CacheType.REDIS or cachetype == "redis":  
            return RedisCacheWrapper(redis_host, redis_password)  
        else:  
            raise ValueError(f"Unsupported cache type: {cachetype}")  
