import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from common import PluginLoader, AgentConfigLoader, ConfigurationError, Context, Task, Plan, PerformanceMonitor
from Config import AppConfig
from common import CommandProcessor, CommandProcessorError, RequestData, UserAction
from userprofiles import UserProfile
from agents import InteractiveAgent
from Invoker.taskinvoker import SmartInvoker, SmartInvokerConfig, TaskExecutionError

@pytest.fixture
def mock_openai_utility():
    with patch('Invoker.taskinvoker.OpenAIUtility') as MockOpenAIUtility:
        yield MockOpenAIUtility.return_value

@pytest.fixture
def mock_cache():
    with patch('Invoker.taskinvoker.BaseCacheWrapper') as MockCache:
        yield MockCache.return_value

@pytest.fixture
def mock_chat_session():
    with patch('Invoker.taskinvoker.ChatSession') as MockChatSession:
        yield MockChatSession.return_value

@pytest.fixture
def mock_app_config():
    with patch('Invoker.taskinvoker.AppConfig') as MockAppConfig:
        mock_instance = MockAppConfig.get_instance.return_value
        mock_instance.GPT_DEPLOYMENT_NAME = 'gpt-4'
        mock_instance.MODULE_NAME = 'Query-Invoker'
        yield mock_instance

@pytest.fixture
def request_data():
    return RequestData(UserId='test_user', UserEmail='test_user@example.com', Query='test_query', RequestId='test_request', IsShowPlanOnly=False)

@pytest.fixture
def query_invoker(mock_openai_utility, mock_cache, mock_chat_session, request_data):
    config = SmartInvokerConfig(agents={'test_agent': {'module': 'test_module', 'class': 'TestClass'}}, retry={'max_retries': 3, 'backoff_factor': 2})
    agents = {'test_agent': MagicMock()}
    planner_prompt = 'test_planner_prompt'
    return SmartInvoker(config, agents, planner_prompt, request_data, mock_cache, 'test_command_prompt_path', mock_chat_session, mock_openai_utility)

@pytest.mark.asyncio
async def test_create(query_invoker, request_data, mock_cache, mock_openai_utility, mock_chat_session):
    with patch('Invoker.taskinvoker.taskinvoker.load_config', new_callable=AsyncMock) as mock_load_config, \
         patch('Invoker.taskinvoker.taskinvoker.load_agents', new_callable=AsyncMock) as mock_load_agents, \
         patch('Invoker.taskinvoker.taskinvoker.load_planner_prompt', new_callable=AsyncMock) as mock_load_planner_prompt:
        mock_load_config.return_value = query_invoker.config
        mock_load_agents.return_value = query_invoker.agents
        mock_load_planner_prompt.return_value = query_invoker.planner_prompt

        Invoker = await SmartInvoker.create(request_data, mock_cache, mock_openai_utility, mock_chat_session, 'test_config_path', 'test_planner_prompt_path', 'test_command_prompt_path')
        assert Invoker.config == query_invoker.config
        assert Invoker.agents == query_invoker.agents
        assert Invoker.planner_prompt == query_invoker.planner_prompt

@pytest.mark.asyncio
async def test_load_config_success():
    with patch('Invoker.taskinvoker.AgentConfigLoader.load', new_callable=AsyncMock) as mock_load:
        mock_load.return_value = {'agents': {}, 'retry': {}, 'version': '1.0', 'last_updated': '2024-01-01', 'cache': {}}
        config = await SmartInvoker.load_config('test_config_path')
        assert config.agents == {}
        assert config.retry == {}
        assert config.version == '1.0'
        assert config.last_updated == '2024-01-01'
        assert config.cache == {}

@pytest.mark.asyncio
async def test_load_config_failure():
    with patch('Invoker.taskinvoker.AgentConfigLoader.load', new_callable=AsyncMock) as mock_load:
        mock_load.side_effect = ConfigurationError('Failed to load configuration')
        with pytest.raises(ConfigurationError):
            await SmartInvoker.load_config('test_config_path')

@pytest.mark.asyncio
async def test_load_agents():
    config = SmartInvokerConfig(agents={'test_agent': {'module': 'test_module', 'class': 'TestClass', 'service_url': 'http://test_url'}}, retry={'max_retries': 3, 'backoff_factor': 2})
    with patch('Invoker.taskinvoker.PluginLoader.load_class') as mock_load_class:
        mock_load_class.return_value = MagicMock()
        agents = await SmartInvoker.load_agents(config)
        assert 'test_agent' in agents

@pytest.mark.asyncio
async def test_resolve_dependencies(query_invoker, mock_app_config):
    task = Task(step=1, agent_name='test_agent', agent_payload={}, dependencies=[('param', 2)])
    completed_tasks = {2: 'completed_task_content'}
    query_invoker.openai_utility.generate_completion = AsyncMock(return_value='resolved_value')
    resolved_task = await query_invoker.resolve_dependencies(task, completed_tasks)
    assert resolved_task.agent_payload['param'] == 'resolved_value'

@pytest.mark.asyncio
async def test_delegate_task(query_invoker, mock_app_config):
    task = Task(step=1, agent_name='test_agent', agent_payload={})
    query_invoker.delegate_task = AsyncMock(return_value='task_result')
    context = Context()
    status_callback = MagicMock()
    agent = query_invoker.agents['test_agent']
    result = await query_invoker.delegate_task(task, context, status_callback)
    assert result == 'task_result'

@pytest.mark.asyncio
async def test_generate_plan(query_invoker, mock_app_config):
    query_invoker.openai_utility.generate_completion = AsyncMock(return_value='{"ActionType": "Execute", "ExecutePlan": [{"Step": 1, "Agent name": "test_agent", "Agent payload": {}, "Status Message": "test_status"}]}')
    plan = await query_invoker.generate_plan()
    assert isinstance(plan, Plan)
    assert len(plan.get_tasks) == 1

@pytest.mark.asyncio
async def test_execute_plan(query_invoker, mock_app_config):
    plan = Plan()
    task = Task(step=1, agent_name='test_agent', agent_payload={}, status_message='test_status')
    plan.add_task(task)
    status_callback = MagicMock()
    query_invoker.resolve_dependencies = AsyncMock(return_value=task)
    query_invoker.delegate_task = AsyncMock(return_value='task_result')
    query_invoker.process_multi_step_result = AsyncMock(return_value='processed_result')

    result = await query_invoker.execute_plan(plan, status_callback)
    assert result == 'task_result'

@pytest.mark.asyncio
async def test_review_session_history(query_invoker):
    # This function is a placeholder and does not have any implementation
    await query_invoker.review_session_history()

@pytest.mark.asyncio
async def test_process_multi_step_result(query_invoker, mock_app_config):
    result = 'multi_step_result'
    query_invoker.openai_utility.generate_completion = AsyncMock(return_value='final_result')

    final_result = await query_invoker.process_multi_step_result(result)
    assert final_result == 'final_result'

@pytest.mark.asyncio
async def test_process_command(query_invoker):
    command_processor = MagicMock()
    command_processor.validate_and_extract_command = AsyncMock(return_value='command_result')
    with patch('Invoker.taskinvoker.CommandProcessor', return_value=command_processor):
        result = await query_invoker.process_command()
        assert result == 'command_result'

@pytest.mark.asyncio
async def test_handle_request(query_invoker, mock_app_config):
    request = MagicMock()
    status_callback = MagicMock()
    query_invoker.process_command = AsyncMock(return_value=None)
    query_invoker.generate_plan = AsyncMock(return_value=Plan())
    query_invoker.execute_plan = AsyncMock(return_value='execution_result')

    result = await query_invoker.handle_request(request, status_callback)
    assert result == 'execution_result'
    query_invoker.chat_session.append_to_user_history_system_message.assert_called_once_with(
        query_invoker.user_id, "Query Execution Plan Generated", str(query_invoker.generate_plan.return_value)
    )