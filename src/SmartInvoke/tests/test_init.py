import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json
import os
from datetime import datetime, timezone
from SmartInvoke import (
    read_file_async, clean_and_convert_to_dict, parse_response, get_app_config,
    initialize_cache, initialize_openai_utility, initialize_chat_session,
    generate_next_query_suggestion, handle_request, Invoker, main
)
import azure.functions as func
from common import RequestData  # Import the RequestData class

@pytest_asyncio.fixture
async def mock_app_config():
    mock_config = MagicMock()
    mock_config.REDIS_HOST = 'localhost'
    mock_config.REDIS_PASSWORD = 'password'
    mock_config.OPENAI_API_BASE = 'https://api.openai.com'
    mock_config.OPENAI_API_KEY = 'key'
    mock_config.OPENAI_API_VERSION = 'v1'
    mock_config.COSMOS_ENDPOINT = 'https://cosmosdb.com'
    mock_config.COSMOS_CONTAINER_NAME = 'container'
    mock_config.COSMOS_DB_NAME = 'database'
    mock_config.GENERATE_QUERY_SUGGESTIONS = True
    mock_config.GPT_4 = 'gpt-4'
    mock_config.USE_CACHE = True
    return mock_config

@pytest_asyncio.fixture
async def mock_request_data():
    return RequestData(
        UserId="user123",
        UserEmail="user@example.com",
        Query="What is the weather today?",
        RequestId="req123",
        IsShowPlanOnly=False
    )

@pytest_asyncio.fixture
async def mock_request(mock_request_data):
    req = MagicMock()
    req.get_json.return_value = mock_request_data.__dict__  # Convert to dictionary
    return req

def test_clean_and_convert_to_dict():
    service_response = '{"key": "value"}'
    result = clean_and_convert_to_dict(service_response)
    assert result == {"key": "value"}

@pytest.mark.asyncio
async def test_parse_response():
    service_response = '{"TextResponse": "Hello", "ResponseType": "text"}'
    result = await parse_response(service_response)
    assert result == ("Hello", "text")

def test_get_app_config(mock_app_config):
    with patch('SmartInvoke.AppConfig.get_instance', return_value=mock_app_config):
        config = get_app_config()
        assert config == mock_app_config

def test_initialize_cache(mock_app_config):
    with patch('SmartInvoke.CacheFactory.get_cache', return_value=MagicMock()) as mock_get_cache:
        cache = initialize_cache(mock_app_config)
        assert cache is not None
        mock_get_cache.assert_called_once()

def test_initialize_chat_session(mock_app_config):
    session = initialize_chat_session(mock_app_config)
    assert session is not None

@pytest.mark.asyncio
async def test_Invoker(mock_request, mock_app_config, mock_request_data):
    with patch('SmartInvoke.get_app_config', return_value=mock_app_config), \
         patch('SmartInvoke.initialize_cache', return_value=MagicMock()), \
         patch('SmartInvoke.initialize_openai_utility', return_value=MagicMock()), \
         patch('SmartInvoke.initialize_chat_session', return_value=MagicMock()), \
         patch('SmartInvoke.SmartInvoke.create', new_callable=AsyncMock, return_value=MagicMock()), \
         patch('SmartInvoke.handle_request', new_callable=AsyncMock, return_value=func.HttpResponse("response", status_code=200)):
        result = await Invoker(mock_request)
        assert result.status_code == 200

@pytest.mark.asyncio
async def test_main(mock_request):
    with patch('SmartInvoke.Invoker', new_callable=AsyncMock, return_value=func.HttpResponse("response", status_code=200)):
        result = await main(mock_request)
        assert result.status_code == 200