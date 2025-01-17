import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken
from agents.dynamic import DynamicAgent, AuthTypeNotSupported  
from Config import AppConfig

@pytest.fixture
def mock_appconfig():
    with patch('agents.dynamic.AppConfig') as MockAppConfig:
        mock_instance = MockAppConfig.get_instance.return_value
        mock_instance.TENANT_ID = 'test_tenant_id'
        mock_instance.TENANT_CLIENTID = 'test_client_id'
        mock_instance.fetch_secret_value_from_keyvault = MagicMock(return_value='test_key_value')
        yield mock_instance

@pytest.fixture
def mock_default_azure_credential():
    with patch('agents.dynamic.DefaultAzureCredential') as MockCredential:
        mock_credential = MockCredential.return_value
        mock_credential.get_token = AsyncMock(return_value=AccessToken(token='test_access_token', expires_on=9999999999))
        yield mock_credential

@pytest.fixture
def mock_async_get_service_response():
    with patch('agents.dynamic.async_get_service_response', new_callable=AsyncMock) as mock_method:
        yield mock_method

@pytest.fixture
def mock_logger():
    with patch('agents.dynamic.logging') as mock_logger:
        yield mock_logger

@pytest.fixture
def test_agent(mock_appconfig):
    agent_info = {
        'authentication': {'type': 'API Key', 'key_vault_secret_name': 'test_secret'},
        'request_template': {},
        'required_fields': ['field1', 'field2']
    }
    return DynamicAgent(name="TestAgent", service_url="http://test_service_url", agent_info=agent_info)

@pytest.mark.asyncio
async def test_perform_task_unsupported_auth(test_agent):
    test_agent.authentication['type'] = 'Unsupported'
    context = {'field1': 'value1', 'field2': 'value2'}
    with pytest.raises(AuthTypeNotSupported):
        await test_agent.perform_task(context)

def test_validate_context_success(test_agent):
    context = {'field1': 'value1', 'field2': 'value2'}
    test_agent.validate_context(context)  # Should not raise an exception

def test_validate_context_missing_field(test_agent):
    context = {'field1': 'value1'}
    with pytest.raises(ValueError, match="Missing required field: field2"):
        test_agent.validate_context(context)

@pytest.mark.asyncio
async def test_quote_values(test_agent):
    input_dict = {'key1': 123, 'key2': 'value2'}
    quoted_dict = await test_agent.quote_values(input_dict)
    assert quoted_dict == {'key1': '123', 'key2': 'value2'}