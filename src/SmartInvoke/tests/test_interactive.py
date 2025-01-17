import pytest
from unittest.mock import patch, MagicMock
from agents.interactive import InteractiveAgent  

@pytest.fixture
def mock_logger():
    with patch('agents.interactive.logger') as mock_logger:
        yield mock_logger

@pytest.fixture
def test_agent():
    return InteractiveAgent(name="TestAgent", service_url="http://test_service_url")

@pytest.mark.asyncio
async def test_perform_task_success(test_agent, mock_logger):
    context = {'UserMessage': 'Hello, World!'}
    response = await test_agent.perform_task(context)
    assert response == 'Hello, World!'
    mock_logger.info.assert_called_with("InteractiveAgent returning UserMessage: Hello, World!")

@pytest.mark.asyncio
async def test_perform_task_no_user_message(test_agent):
    context = {}
    with pytest.raises(ValueError, match="No UserMessage found in context"):
        await test_agent.perform_task(context)

def test_agent_properties(test_agent):
    assert test_agent.agent_name == "TestAgent"
    assert test_agent.agent_url == "http://test_service_url"
    assert test_agent.agent_max_retries == 3
    assert test_agent.agent_backoff_factor == 2
    assert test_agent.agent_is_initialized is False