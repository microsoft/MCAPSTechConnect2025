import os
import aiofiles
import logging
from dataclasses import dataclass, field
from typing import Dict
from contextlib import asynccontextmanager
import asyncio
from Config.configuration import AppConfig
from common.openai_utils import OpenAIUtility


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Commands:
    """Class to store available commands."""
    NEW_SESSION_COMMAND: str = "new session"
    NEW_TOPIC_COMMAND: str = "new topic"
    CREATE_SUPPORT_TICKET: str = "create support ticket"
    FEEDBACK_POSITIVE: str="feedbackpositive"
    FEEDBACK_NEGATIVE: str="feedbacknegative"
    CONTEXT_COMMAND = {  
                "set context hr": "HR",
                "set context finance": "Finance",
                "set context sales": "Sales",
                "set context judiciary": "Judiciary",
                "set context procurement": "Procurement"
                
            }  
    FORGET_ME_COMMAND: str = "forget me"

@dataclass(frozen=True)
class CommandMessages:
    """Class to store command response messages."""
    NEW_TOPIC_ACTIVATED: str = (
        "📝 New Topic Activated! The canvas is clean, and we're eager to explore a new topic with you. "
        "Go ahead, ask a question."
    )
    CREATE_SUPPORT_TICKET: str = (
        "We're on it! 🚧 Exciting news: we're working on integrating with Case Management. Right now, creating it isn't an option, "
        "but don't worry! 🌟 We'll soon have that capability ready for you!"
    )
    FORGET_ME_ACTIVATED: str = (
        "🚀 Forget Me Activated! Your chat history has been cleared. We're ready to start fresh. Go ahead, ask a question."
    )
    CONTEXT_SET: str = (
        "Current business function context is set to {context}. "
        "If you need to change the context, just type 'Set Context' followed by your desired business function."
    )
    FEEDBACK_POSITIVE: str= (
        " 😊 Thank you for your feedback! I'm glad you liked the response. Is there anything else you would like to know or discuss?"
    )
    FEEDBACK_NEGATIVE: str= (
        "📝 I appreciate your feedback! Could you please let me know what specific information you were looking for or how I can improve my response?"
    )

class CommandProcessorError(Exception):
    """Custom exception class for CommandProcessor errors."""
    pass

class CommandProcessor:
    """Class to process user commands."""

    __slots__ = ('request_id','user_id', 'user_request', 'prompt_library_path', 'chat_session', 'openai_utility')

    def __init__(self,request_id:str, user_id: str, user_request: str, prompt_library_path: str, openai_utility: OpenAIUtility = None):
        self.user_id = user_id
        self.request_id = request_id
        self.user_request = user_request
        self.prompt_library_path = prompt_library_path
        self.openai_utility = openai_utility or OpenAIUtility()

    def __str__(self):
        return f"CommandProcessor(user_id={self.user_id}, user_request={self.user_request})"

    
    async def validate_and_extract_command(self) -> str:
        """Validates and extracts commands from the user request.

        Returns:
            str: Response message based on the extracted command.
        """
        try:
            command_validation_prompt = await self._read_prompt_file()
            command = await self._get_command_from_request(command_validation_prompt)
            logging.info(f'Command Processing Result :{command}')
            if not command or command == "notfound":
                return None

            if command in (Commands.NEW_SESSION_COMMAND, Commands.NEW_TOPIC_COMMAND):
                self.chat_session.clear_chat_history(self.user_id)
                return CommandMessages.NEW_TOPIC_ACTIVATED

            if command == Commands.CREATE_SUPPORT_TICKET:
                return CommandMessages.CREATE_SUPPORT_TICKET

            if command == Commands.FORGET_ME_COMMAND:
                self.chat_session.clear_chat_history(self.user_id)
                return CommandMessages.FORGET_ME_ACTIVATED

            if command == Commands.FEEDBACK_POSITIVE:
                return CommandMessages.FEEDBACK_POSITIVE
            
            if command == Commands.FEEDBACK_NEGATIVE:
                return CommandMessages.FEEDBACK_NEGATIVE
            
            if command in Commands.CONTEXT_COMMAND:
                context = Commands.CONTEXT_COMMAND[command]
                loop = asyncio.get_running_loop()
                
                result =await loop.run_in_executor(None, self._process_context_command, context)

                return result

            return command

        except Exception as e:
            logger.error(f"Error in validate_and_extract_command: {e}")
            raise CommandProcessorError("An error occurred while processing the command. Please try again later.")

    @asynccontextmanager
    async def _open_file(self, path: str, mode: str):
        """Asynchronous context manager for opening files."""
        async with aiofiles.open(path, mode) as file:
            yield file

    async def _read_prompt_file(self) -> str:
        """Reads the command validation prompt from a file.

        Returns:
            str: Content of the command validation prompt file.
        """
        prompt_path = os.path.join(self.prompt_library_path)
        async with self._open_file(prompt_path, 'r') as file:
            return await file.read()

    async def _get_command_from_request(self, command_validation_prompt: str) -> str:
        """Gets the command from the user request using OpenAI utility.

        Args:
            command_validation_prompt (str): The prompt for command validation.

        Returns:
            str: The extracted command.
        """
        app_config = AppConfig.get_instance()
        messages = [
            {"role": "system", "content": command_validation_prompt},
            {"role": "user", "content": self.user_request}
        ]
        return await self.openai_utility.generate_completion(prompt=messages,gpt_deployment_name= app_config.GPT_4,conversation_id=self.request_id,request_id = self.request_id)

    def _process_context_command(self, context: str) -> str:
        """Processes context-setting commands.

        Args:
            context (str): The context to set.

        Returns:
            str: Response message after setting the context.
        """
        try:
            answer = CommandMessages.CONTEXT_SET.format(context=context)
            return answer

        except Exception as e:
            logger.error(f"Error in _process_context_command: {e}")
            raise CommandProcessorError("An error occurred while processing the context command. Please try again later.")

