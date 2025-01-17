import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from agents.agent import BaseAgent 

class TestAgent(BaseAgent):
    async def perform_task(self, context):
        pass

@pytest.fixture
def mock_async_get_service_response():
    with patch('agents.agent.async_get_service_response', new_callable=AsyncMock) as mock_method:
        yield mock_method

@pytest.fixture
def mock_logger():
    with patch('agents.agent.logger') as mock_logger:
        yield mock_logger

@pytest.fixture
def test_agent():
    return TestAgent(name="TestAgent", service_url="http://test_service_url")

@pytest.mark.asyncio
async def test_initialize(test_agent, mock_logger):
    await test_agent.initialize()
    assert test_agent.is_initialized is True
    mock_logger.info.assert_called_with("Agent TestAgent initialized.")

@pytest.mark.asyncio
async def test_terminate(test_agent, mock_logger):
    await test_agent.terminate()
    assert test_agent.is_initialized is False
    mock_logger.info.assert_called_with("Agent TestAgent terminated.")

def test_agent_properties(test_agent):
    assert test_agent.agent_name == "TestAgent"
    assert test_agent.agent_url == "http://test_service_url"
    assert test_agent.agent_max_retries == 3
    assert test_agent.agent_backoff_factor == 2
    assert test_agent.agent_is_initialized is False

@pytest.mark.asyncio
async def test_call_service_success(test_agent, mock_async_get_service_response):
    mock_async_get_service_response.return_value = "test_response"
    context = {"key": "value"}
    response = await test_agent.call_service(context)
    assert response == "test_response"
    mock_async_get_service_response.assert_called_with("http://test_service_url", context)

@pytest.mark.asyncio
async def test_call_service_retry(test_agent, mock_async_get_service_response):
    mock_async_get_service_response.side_effect = [Exception("Test Exception"), "test_response"]
    context = {"key": "value"}
    response = await test_agent.call_service(context)
    assert response == "test_response"
    assert mock_async_get_service_response.call_count == 2

@pytest.mark.asyncio
async def test_send_message(test_agent):
    target_agent = AsyncMock()
    message = "test_message"
    await test_agent.send_message(target_agent, message)
    target_agent.receive_message.assert_called_with(message)

@pytest.mark.asyncio
async def test_receive_message(test_agent):
    message = "test_message"
    await test_agent.receive_message(message)
    assert await test_agent.message_queue.get() == message

@pytest.mark.asyncio
async def test_process_messages(test_agent):
    message = "test_message"
    await test_agent.receive_message(message)
    await test_agent.process_messages()
    assert test_agent.message_queue.qsize() == 0