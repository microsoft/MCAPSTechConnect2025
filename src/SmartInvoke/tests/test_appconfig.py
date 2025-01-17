import pytest
from unittest.mock import patch, MagicMock
from Config.configuration import AppConfig

@pytest.fixture
def mock_load_config_value():
    with patch.object(BaseAppConfig, 'load_config_value') as mock_method:
        yield mock_method

@pytest.fixture
def mock_load_bool_config_value():
    with patch.object(BaseAppConfig, 'load_bool_config_value') as mock_method:
        yield mock_method

def test_openai_api_key(mock_load_config_value):
    mock_load_config_value.return_value = 'test_key'
    config = AppConfig()
    assert config.OPENAI_API_KEY == 'test_key'
    mock_load_config_value.assert_called_with('OPENAI_API_KEY', None)

def test_openai_api_base(mock_load_config_value):
    mock_load_config_value.return_value = 'test_base'
    config = AppConfig()
    assert config.OPENAI_API_BASE == 'test_base'
    mock_load_config_value.assert_called_with('OPENAI_API_BASE', "")

def test_openai_api_version(mock_load_config_value):
    mock_load_config_value.return_value = 'test_version'
    config = AppConfig()
    assert config.OPENAI_API_VERSION == 'test_version'
    mock_load_config_value.assert_called_with('OPENAI_API_VERSION', "")

def test_gpt_deployment_name(mock_load_config_value):
    mock_load_config_value.return_value = 'test_deployment'
    config = AppConfig()
    assert config.GPT_DEPLOYMENT_NAME == 'test_deployment'
    mock_load_config_value.assert_called_with('GPT_DEPLOYMENT_NAME', "gpt-4o")

def test_module_name(mock_load_config_value):
    mock_load_config_value.return_value = 'test_module'
    config = AppConfig()
    assert config.MODULE_NAME == 'test_module'
    mock_load_config_value.assert_called_with('MODULE_NAME', "Query-Invoker")

def test_gpt_35_turbo(mock_load_config_value):
    mock_load_config_value.return_value = 'test_gpt_35_turbo'
    config = AppConfig()
    assert config.GPT_35_TURBO == 'test_gpt_35_turbo'
    mock_load_config_value.assert_called_with('GPT_35_TURBO', "gpt-35-turbo")

def test_gpt_4_32_model(mock_load_config_value):
    mock_load_config_value.return_value = 'test_gpt_4_32_model'
    config = AppConfig()
    assert config.GPT_4_32_MODEL == 'test_gpt_4_32_model'
    mock_load_config_value.assert_called_with('GPT_4_32_MODEL', "gpt-4-32k")

def test_gpt_4(mock_load_config_value):
    mock_load_config_value.return_value = 'test_gpt_4'
    config = AppConfig()
    assert config.GPT_4 == 'test_gpt_4'
    mock_load_config_value.assert_called_with('GPT_4', "gpt-4o")

def test_use_cache(mock_load_bool_config_value):
    mock_load_bool_config_value.return_value = True
    config = AppConfig()
    assert config.USE_CACHE is True
    mock_load_bool_config_value.assert_called_with('USE_CACHE', False)

def test_use_history(mock_load_bool_config_value):
    mock_load_bool_config_value.return_value = False
    config = AppConfig()
    assert config.USE_HISTORY is False
    mock_load_bool_config_value.assert_called_with('USE_HISTORY', True)

def test_is_permission_check_enabled(mock_load_bool_config_value):
    mock_load_bool_config_value.return_value = True
    config = AppConfig()
    assert config.IS_PERMISSION_CHECK_ENABLED is True
    mock_load_bool_config_value.assert_called_with('IS_PERMISSION_CHECK_ENABLED', False)

def test_cache_type(mock_load_config_value):
    mock_load_config_value.return_value = 'test_cache_type'
    config = AppConfig()
    assert config.CACHE_TYPE == 'test_cache_type'
    mock_load_config_value.assert_called_with('CACHE_TYPE', "redis")

def test_redis_host(mock_load_config_value):
    mock_load_config_value.return_value = 'test_redis_host'
    config = AppConfig()
    assert config.REDIS_HOST == 'test_redis_host'
    mock_load_config_value.assert_called_with('REDIS_HOST', "")

def test_redis_password(mock_load_config_value):
    mock_load_config_value.return_value = 'test_redis_password'
    config = AppConfig()
    assert config.REDIS_PASSWORD == 'test_redis_password'
    mock_load_config_value.assert_called_with('REDIS_PASSWORD', None)

def test_user_history_retrieval_limit(mock_load_config_value):
    mock_load_config_value.return_value = '20'
    config = AppConfig()
    assert config.USER_HISTORY_RETRIEVAL_LIMIT == 20
    mock_load_config_value.assert_called_with('USER_HISTORY_RETRIEVAL_LIMIT', 10)

def test_hr_insight_service_url(mock_load_config_value):
    mock_load_config_value.return_value = 'http://test_hr_insight_service_url'
    config = AppConfig()
    assert config.HR_INSIGHT_SERVICE_URL == 'http://test_hr_insight_service_url'
    mock_load_config_value.assert_called_with('HR_INSIGHT_SERVICE_URL', "http://localhost:9999/api/HRInsightService")

def test_hr_document_generation_service_url(mock_load_config_value):
    mock_load_config_value.return_value = 'http://test_hr_document_generation_service_url'
    config = AppConfig()
    assert config.HR_DOCUMENT_GENERATION_SERVICE_URL == 'http://test_hr_document_generation_service_url'
    mock_load_config_value.assert_called_with('HR_DOCUMENT_GENERATION_SERVICE_URL', "http://localhost:5555/api/HRDocGen")

def test_cosmos_endpoint(mock_load_config_value):
    mock_load_config_value.return_value = 'test_cosmos_endpoint'
    config = AppConfig()
    assert config.COSMOS_ENDPOINT == 'test_cosmos_endpoint'
    mock_load_config_value.assert_called_with('COSMOS_ENDPOINT', "")

def test_cosmos_db_name(mock_load_config_value):
    mock_load_config_value.return_value = 'test_cosmos_db_name'
    config = AppConfig()
    assert config.COSMOS_DB_NAME == 'test_cosmos_db_name'
    mock_load_config_value.assert_called_with('COSMOS_DB_NAME', "")

def test_cosmos_container_name(mock_load_config_value):
    mock_load_config_value.return_value = 'test_cosmos_container_name'
    config = AppConfig()
    assert config.COSMOS_CONTAINER_NAME == 'test_cosmos_container_name'
    mock_load_config_value.assert_called_with('COSMOS_CONTAINER_NAME', "")

def test_azure_tenant_id(mock_load_config_value):
    mock_load_config_value.return_value = 'test_azure_tenant_id'
    config = AppConfig()
    assert config.AZURE_TENANT_ID == 'test_azure_tenant_id'
    mock_load_config_value.assert_called_with('AZURE_TENANT_ID', "")

def test_user_profile_client_id(mock_load_config_value):
    mock_load_config_value.return_value = 'test_user_profile_client_id'
    config = AppConfig()
    assert config.USER_PROFILE_CLIENT_ID == 'test_user_profile_client_id'
    mock_load_config_value.assert_called_with('USER_PROFILE_CLIENT_ID', "")

def test_user_profile_client_secret(mock_load_config_value):
    mock_load_config_value.return_value = 'test_user_profile_client_secret'
    config = AppConfig()
    assert config.USER_PROFILE_CLIENT_SECRET == 'test_user_profile_client_secret'
    mock_load_config_value.assert_called_with('USER_PROFILE_CLIENT_SECRET', "")

def test_include_user_profile(mock_load_bool_config_value):
    mock_load_bool_config_value.return_value = True
    config = AppConfig()
    assert config.INCLUDE_USER_PROFILE is True
    mock_load_bool_config_value.assert_called_with('INCLUDE_USER_PROFILE', False)

def test_generate_query_suggestions(mock_load_bool_config_value):
    mock_load_bool_config_value.return_value = False
    config = AppConfig()
    assert config.GENERATE_QUERY_SUGGESTIONS is False
    mock_load_bool_config_value.assert_called_with('GENERATE_QUERY_SUGGESTIONS', True)

def test_process_commands(mock_load_bool_config_value):
    mock_load_bool_config_value.return_value = False
    config = AppConfig()
    assert config.PROCESS_COMMANDS is False
    mock_load_bool_config_value.assert_called_with('PROCESS_COMMANDS', True)

def test_tenant_id(mock_load_config_value):
    mock_load_config_value.return_value = 'test_tenant_id'
    config = AppConfig()
    assert config.TENANT_ID == 'test_tenant_id'
    mock_load_config_value.assert_called_with('TENANT_ID', "")

def test_tenant_clientid(mock_load_config_value):
    mock_load_config_value.return_value = 'test_tenant_clientid'
    config = AppConfig()
    assert config.TENANT_CLIENTID == 'test_tenant_clientid'
    mock_load_config_value.assert_called_with('TENANT_CLIENTID', "")