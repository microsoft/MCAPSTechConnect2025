import logging  
from .agent import BaseAgent  

logger = logging.getLogger(__name__)  

class InteractiveAgent(BaseAgent):  
    def __init__(self, name, service_url=None, max_retries=None, backoff_factor=None, session=None):  
        super().__init__(name, service_url, max_retries, backoff_factor, session)  

    async def perform_task(self, context):  
        user_message = context.get("UserMessage")  
        if not user_message:  
            raise ValueError("No UserMessage found in context")  

        logger.info(f"InteractiveAgent returning UserMessage: {user_message}")  
        return user_message  
