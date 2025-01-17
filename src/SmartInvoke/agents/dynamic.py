import json  
import logging  
import aiohttp  
from .agent import BaseAgent  
from Config import AppConfig
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken
  
class AuthTypeNotSupported(Exception):  
    pass  
  
class DynamicAgent(BaseAgent):  
    def __init__(self, name, service_url, agent_info, max_retries=None, backoff_factor=None, session=None):  
        super().__init__(name, service_url, max_retries, backoff_factor, session)  
        if agent_info:  
            self.authentication = agent_info.get('authentication', {})  
            self.request_template = agent_info.get('request_template', {})  
            self.required_fields = agent_info.get('required_fields', []) 
  
    @property  
    def agent_authentication(self):  
        return self.authentication  
  
    @property  
    def agent_request_template(self):  
        return self.request_template  
  
    @property  
    def agent_required_fields(self):  
        return self.required_fields
  
    def validate_context(self, context):  
        for field in self.required_fields:  
            if field not in context:  
                raise ValueError(f"Missing required field: {field}")  
  
    async def perform_task(self, context):  
        self.validate_context(context)  
        appconfig = AppConfig.get_instance()  
        auth_type = self.authentication.get('type')  
        context['auth_type'] = auth_type
        access_token = None 

        

        if auth_type == 'API Key':  
            key_name = self.authentication.get('key_vault_secret_name')  
            key_value = appconfig.fetch_secret_value_from_keyvault(key_name)  
            if key_value is None:  
                logging.info(f"Key {key_name} not found in key vault")  
                service_url = self.service_url  
            else:  
                service_url = self.service_url + f'?code={key_value}'  
        elif auth_type == 'Managed Identity':  
            context['ManagedIdentity'] = True  
            service_url = self.service_url 
        else:  
            raise AuthTypeNotSupported("Unsupported authentication type")  
  
        request_data = context  
        request_data = await self.quote_values(request_data)  
        request_data = json.dumps(request_data)

        # Generate token
        tenant_id = appconfig.TENANT_ID
        client_id =  appconfig.TENANT_CLIENTID
        credential = DefaultAzureCredential(authority=f"https://login.microsoftonline.com/{tenant_id}")
        token_request_context = [f"api://{client_id}/.default"]
        token: AccessToken = credential.get_token(*token_request_context)
        access_token = token.token
        logging.info(f"Access Token generated for {self.service_url}")
        response = await async_get_service_response(service_url, request_data, access_token)  
  
        # Process any incoming messages  
        await self.process_messages()  
  
        return response  
  
    async def quote_values(self, input_dict):  
        # Iterate through the dictionary and quote the values  
        quoted_dict = {key: f"{value}" if not isinstance(value, str) else f"{value}" for key, value in input_dict.items()}  
        return quoted_dict  