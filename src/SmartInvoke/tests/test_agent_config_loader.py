import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os
import aiofiles
import asyncio
from common.agent_config_loader import AgentConfigLoader, ConfigurationError 

@pytest.fixture
def mock_os_path_exists():
    with patch('common.agent_config_loader.os.path.exists') as mock_exists:
        yield mock_exists

@pytest.fixture
def mock_aiofiles_open():
    with patch('common.agent_config_loader.aiofiles.open', new_callable=AsyncMock) as mock_open:
        yield mock_open

@pytest.fixture
def mock_asyncio_sleep():
    with patch('common.agent_config_loader.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        yield mock_sleep

@pytest.fixture
def mock_logger():
    with patch('common.agent_config_loader.logging') as mock_logger:
        yield mock_logger

@pytest.mark.asyncio
async def test_load_from_file_not_exist(mock_os_path_exists):
    mock_os_path_exists.return_value = False
    with pytest.raises(ConfigurationError, match="Configuration file test_path does not exist."):
        await AgentConfigLoader.load(config_path='test_path')

@pytest.mark.asyncio
async def test_load_from_cosmosdb_failure(mock_asyncio_sleep):
    with pytest.raises(ConfigurationError, match="Failed to query Cosmos DB for configuration."):
        await AgentConfigLoader.load()

@pytest.mark.asyncio
async def test_validate_config_missing_agents():
    config = {}
    with pytest.raises(ConfigurationError, match="Configuration from test_source is missing 'agents' key."):
        await AgentConfigLoader._validate_config(config, 'test_source')

@pytest.mark.asyncio
async def test_validate_config_missing_module_or_class():
    config = {
        'agents': {'agent1': {}}
    }
    with pytest.raises(ConfigurationError, match="Agent 'agent1' in test_source is missing 'module' or 'class' key."):
        await AgentConfigLoader._validate_config(config, 'test_source')

@pytest.mark.asyncio
async def test_validate_config_success(mock_logger):
    config = {
        'agents': {'agent1': {'module': 'module1', 'class': 'class1'}}
    }
    validated_config = await AgentConfigLoader._validate_config(config, 'test_source')
    assert 'retry' in validated_config
    assert 'cache' in validated_config
    mock_logger.info.assert_called_with("Configuration loaded from test_source")