import json  
import logging  
from dataclasses import dataclass, field  
import os
from typing import Optional, Dict  
from Config.configuration import AppConfig  
from azure.identity.aio import ClientSecretCredential  
from msgraph.graph_service_client import GraphServiceClient  
from msgraph.generated.models.user import User  
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder

from common.cache_utils import BaseCacheWrapper, CacheFactory, CacheType
from common.functions import generate_cache_key

# Update with the required user profile attributes  
USER_PROFILE_ATTRIBUTES = {  
    'Country': 'country',  
    'Role': 'employee_type'  
}  

@dataclass  
class UserProfile:  
    user_id: str  
    user: Optional[User] = field(default=None, init=False)  
    config: Optional[AppConfig] = field(default=None, init=False)  
    cache: Optional[BaseCacheWrapper] = field(default=None, init=False)  

    def __post_init__(self):  
        self.config :AppConfig = AppConfig.get_instance()  
        self.cache :Optional[BaseCacheWrapper] = self._initialize_cache()  

    def _initialize_cache(self) -> Optional[BaseCacheWrapper]:  
        if self.config.USE_CACHE:  
            return CacheFactory.get_cache(  
                cachetype=CacheType.REDIS,  
                redis_host=self.config.REDIS_HOST,  
                redis_password=os.getenv('REDIS_PASSWORD') if os.getenv('REDIS_PASSWORD') else None,  
            )  
        return None  

    async def _initialize_credential(self) -> ClientSecretCredential:  
        return ClientSecretCredential(  
            tenant_id=self.config.AZURE_TENANT_ID,  
            client_id=self.config.USER_PROFILE_CLIENT_ID,  
            client_secret=self.config.USER_PROFILE_CLIENT_SECRET  
        )  

    async def fetch_user_profile(self) -> User:  
        scope = ['https://graph.microsoft.com/.default']  
        try:  
            credential = await self._initialize_credential()  
            user_client = GraphServiceClient(credential, scope)  
            query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(  
                select=list(USER_PROFILE_ATTRIBUTES.keys())  
            )  
            request_configuration = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(  
                query_parameters=query_params  
            )  
            self.user = await user_client.users.by_user_id(self.user_id).get(request_configuration)  
            return self.user  
        except Exception as e:  
            logging.error(f"Failed to fetch user profile for user_id {self.user_id}: {e}")  
            raise  

    async def get_user_details_filter_search_index(self) -> Optional[str]:  
        filter_criteria = []  
        cache_key = generate_cache_key(self.user_id, "User Profile Search Attribute", self.config.is_permission_check_enabled)  
        if self.config.is_permission_check_enabled:  
            try:  
                filter_criteria_string = self.cache.read_from_cache(cache_key) if self.cache else None  
                if filter_criteria_string:  
                    filter_criteria = json.loads(filter_criteria_string)  
                else:  
                    user_details = await self.fetch_user_profile()  
                    if user_details:  
                        user_profile_data = {  
                            attribute: getattr(user_details, property_name)  
                            for attribute, property_name in USER_PROFILE_ATTRIBUTES.items()  
                        }  
                        filter_criteria = [  
                            f"{attribute} eq '{value}'"  
                            for attribute, value in user_profile_data.items()  
                        ]  
                        filter_criteria_string = json.dumps(filter_criteria)  
                        if self.cache:  
                            self.cache.write_to_cache(cache_key, filter_criteria_string, 60000)  
            except Exception as e:  
                logging.error(f"Error fetching or caching user details for user_id {self.user_id}: {e}")  
                raise  
        if filter_criteria:  
            return ' and '.join(filter_criteria)  
        return None  

    async def get_user_profile_attributes(self) -> Optional[Dict[str, str]]:  
        cache_key = generate_cache_key(self.user_id, "User Profile Attributes",True)  
        try:  
            # Attempt to retrieve from cache  
            cached_data = self.cache.read_from_cache(cache_key) if self.cache else None  
            if cached_data:  
                return json.loads(cached_data)  

            # If not in cache, fetch from Graph API  
            user_details = await self.fetch_user_profile()  
            if user_details:  
                user_profile_data = {  
                    attribute: getattr(user_details, property_name, None)  
                    for attribute, property_name in USER_PROFILE_ATTRIBUTES.items()  
                }  
                # Store in cache  
                if self.cache:  
                    self.cache.write_to_cache(cache_key, json.dumps(user_profile_data), 60000)  
                return user_profile_data  
        except Exception as e:  
            logging.error(f"Failed to get user profile attributes for user_id {self.user_id}: {e}")  
            raise  
        return None  
