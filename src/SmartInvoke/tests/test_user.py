import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass, field
from typing import Optional, Dict
from Config.configuration import AppConfig
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.user import User
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
from userprofiles.user import UserProfile  

@pytest.fixture
def mock_app_config():
    with patch('userprofiles.user.AppConfig') as MockAppConfig:
        mock_instance = MockAppConfig.get_instance.return_value
        mock_instance.USE_CACHE = True
        mock_instance.REDIS_HOST = 'test_redis_host'
        mock_instance.AZURE_TENANT_ID = 'test_tenant_id'
        mock_instance.USER_PROFILE_CLIENT_ID = 'test_client_id'
        mock_instance.USER_PROFILE_CLIENT_SECRET = 'test_client_secret'
        yield mock_instance

@pytest.fixture
def mock_cache():
    with patch('userprofiles.user.CacheFactory.get_cache') as MockCacheFactory:
        mock_cache = MockCacheFactory.return_value
        yield mock_cache

@pytest.fixture
def user_profile(mock_app_config, mock_cache):
    return UserProfile(user_id='test_user')

@pytest.mark.asyncio
async def test_initialize_cache(user_profile, mock_cache):
    assert user_profile.cache == mock_cache

@pytest.mark.asyncio
async def test_initialize_credential(user_profile):
    with patch('userprofiles.user.ClientSecretCredential') as MockCredential:
        credential = await user_profile._initialize_credential()
        MockCredential.assert_called_with(
            tenant_id='test_tenant_id',
            client_id='test_client_id',
            client_secret='test_client_secret'
        )
        assert credential == MockCredential.return_value

@pytest.mark.asyncio
async def test_fetch_user_profile(user_profile):
    mock_credential = AsyncMock()
    mock_user_client = MagicMock()
    mock_user = MagicMock()
    with patch('userprofiles.user.ClientSecretCredential', return_value=mock_credential), \
         patch('userprofiles.user.GraphServiceClient', return_value=mock_user_client):
        mock_user_client.users.by_user_id.return_value.get = AsyncMock(return_value=mock_user)
        user = await user_profile.fetch_user_profile()
        assert user == mock_user

@pytest.mark.asyncio
async def test_get_user_details_filter_search_index(user_profile, mock_cache):
    mock_cache.read_from_cache.return_value = None
    mock_user = MagicMock()
    mock_user.country = 'USA'
    mock_user.employee_type = 'Engineer'
    user_profile.fetch_user_profile = AsyncMock(return_value=mock_user)
    filter_criteria = await user_profile.get_user_details_filter_search_index()
    assert filter_criteria == "Country eq 'USA' and Role eq 'Engineer'"

@pytest.mark.asyncio
async def test_get_user_profile_attributes(user_profile, mock_cache):
    mock_cache.read_from_cache.return_value = None
    mock_user = MagicMock()
    mock_user.country = 'USA'
    mock_user.employee_type = 'Engineer'
    user_profile.fetch_user_profile = AsyncMock(return_value=mock_user)
    user_profile_data = await user_profile.get_user_profile_attributes()
    assert user_profile_data == {'Country': 'USA', 'Role': 'Engineer'}