import pytest
from unittest.mock import AsyncMock, Mock, patch
from common.commandidentification import CommandProcessor, CommandProcessorError, Commands, CommandMessages  # Update module path
from Config.configuration import AppConfig

class TestCommandProcessor(CommandProcessor):
    async def _read_prompt_file(self):
        return "Validation prompt"

    async def _get_command_from_request(self):
        return Commands.NEW_TOPIC_COMMAND

@pytest.fixture
def command_processor():
    chat_session_mock = Mock(spec=ChatSession)
    openai_utility_mock = Mock(spec=OpenAIUtility)
    return TestCommandProcessor(
        request_id="test_request_id",
        user_id="test_user_id",
        user_request="new topic",
        prompt_library_path="/mock/path",
        chat_session=chat_session_mock,
        openai_utility=openai_utility_mock
    )

@pytest.mark.asyncio
async def test_validate_and_extract_command_new_topic(command_processor):
    # Arrange
    with patch.object(command_processor, "_read_prompt_file", AsyncMock(return_value="Validation prompt")), \
         patch.object(command_processor, "_get_command_from_request", AsyncMock(return_value=Commands.NEW_TOPIC_COMMAND)):
        command_processor.chat_session.clear_chat_history = Mock()

        # Act
        response = await command_processor.validate_and_extract_command()

        # Assert
        assert response == CommandMessages.NEW_TOPIC_ACTIVATED
        command_processor.chat_session.clear_chat_history.assert_called_once_with(command_processor.user_id)


@pytest.mark.asyncio
async def test_validate_and_extract_command_create_support_ticket(command_processor):
    # Arrange
    with patch.object(command_processor, "_read_prompt_file", AsyncMock(return_value="Validation prompt")), \
         patch.object(command_processor, "_get_command_from_request", AsyncMock(return_value=Commands.CREATE_SUPPORT_TICKET)):
        
        # Act
        response = await command_processor.validate_and_extract_command()

        # Assert
        assert response == CommandMessages.CREATE_SUPPORT_TICKET


@pytest.mark.asyncio
async def test_validate_and_extract_command_forget_me(command_processor):
    # Arrange
    with patch.object(command_processor, "_read_prompt_file", AsyncMock(return_value="Validation prompt")), \
         patch.object(command_processor, "_get_command_from_request", AsyncMock(return_value=Commands.FORGET_ME_COMMAND)):
        command_processor.chat_session.clear_chat_history = Mock()

        # Act
        response = await command_processor.validate_and_extract_command()

        # Assert
        assert response == CommandMessages.FORGET_ME_ACTIVATED
        command_processor.chat_session.clear_chat_history.assert_called_once_with(command_processor.user_id)


@pytest.mark.asyncio
async def test_validate_and_extract_command_context(command_processor):
    # Arrange
    with patch.object(command_processor, "_read_prompt_file", AsyncMock(return_value="Validation prompt")), \
         patch.object(command_processor, "_get_command_from_request", AsyncMock(return_value="set context hr")):
        command_processor._process_context_command = Mock(return_value=CommandMessages.CONTEXT_SET.format(context="HR"))

        # Act
        response = await command_processor.validate_and_extract_command()

        # Assert
        assert response == CommandMessages.CONTEXT_SET.format(context="HR")
        command_processor._process_context_command.assert_called_once_with("HR")


@pytest.mark.asyncio
async def test_validate_and_extract_command_no_command_found(command_processor):
    # Arrange
    with patch.object(command_processor, "_read_prompt_file", AsyncMock(return_value="Validation prompt")), \
         patch.object(command_processor, "_get_command_from_request", AsyncMock(return_value="notfound")):

        # Act
        response = await command_processor.validate_and_extract_command()

        # Assert
        assert response is None


@pytest.mark.asyncio
async def test_validate_and_extract_command_exception_handling(command_processor):
    # Arrange
    with patch.object(command_processor, "_read_prompt_file", AsyncMock(side_effect=Exception("File read error"))):

        # Act & Assert
        with pytest.raises(CommandProcessorError, match="An error occurred while processing the command. Please try again later."):
            await command_processor.validate_and_extract_command()


@pytest.mark.asyncio
async def test_read_prompt_file(command_processor):
    # Arrange
    with patch("aiofiles.open", new_callable=AsyncMock) as mock_open:
        mock_file = mock_open.return_value.__aenter__.return_value
        mock_file.read.return_value = "Mocked prompt content"

        # Act
        content = await command_processor._read_prompt_file()

        # Assert
        assert content == "Validation prompt"


def test_process_context_command(command_processor):
    # Arrange
    command_processor.chat_session.clear_chat_history = Mock()
    command_processor.chat_session.get_current_domain_context = Mock(return_value="General")
    command_processor.chat_session.append_to_user_history = Mock()
    command_processor.chat_session.set_current_domain_context = Mock()

    # Act
    response = command_processor._process_context_command("HR")

    # Assert
    assert response == CommandMessages.CONTEXT_SET.format(context="HR")
    command_processor.chat_session.clear_chat_history.assert_called_once_with(command_processor.user_id)
    command_processor.chat_session.append_to_user_history.assert_called_once_with(
        user_id=command_processor.user_id, question=command_processor.user_request, answer=response
    )
    command_processor.chat_session.set_current_domain_context.assert_called_once_with(
        user_id=command_processor.user_id, context="HR"
    )


def test_process_context_command_no_change(command_processor):
    # Arrange
    command_processor.chat_session.get_current_domain_context = Mock(return_value="HR")

    # Act
    response = command_processor._process_context_command("HR")

    # Assert
    assert response is None