import asyncio
import json  
import aiohttp  
import logging  
from abc import ABC, abstractmethod  
from circuitbreaker import circuit  
from tenacity import retry, stop_after_attempt, wait_exponential  
logger = logging.getLogger(__name__)  

class BaseAgent(ABC):  
    MAX_RETRIES = 3  
    BACKOFF_FACTOR = 2  

    def __init__(self, name, service_url, max_retries=None, backoff_factor=None, session=None):  
        self.name = name  
        self.service_url = service_url  
        self.max_retries = max_retries or self.MAX_RETRIES  
        self.backoff_factor = backoff_factor or self.BACKOFF_FACTOR  
        self.is_initialized = False  
        self.message_queue = asyncio.Queue()  

    @property  
    def agent_name(self):  
        return self.name  

    @property  
    def agent_url(self):  
        return self.service_url  

    @property  
    def agent_max_retries(self):  
        return self.max_retries  

    @property  
    def agent_backoff_factor(self):  
        return self.backoff_factor  

    @property  
    def agent_is_initialized(self):  
        return self.is_initialized  

    async def initialize(self):  
        self.is_initialized = True  
        logger.info(f"Agent {self.__class__.__name__} initialized.")  

    async def terminate(self):  
        self.is_initialized = False  
        logger.info(f"Agent {self.__class__.__name__} terminated.")  

    @abstractmethod  
    async def perform_task(self, context):  
        pass  

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))  
    @circuit(failure_threshold=3, recovery_timeout=10)  
    async def call_service(self, context):  
        logging.info(f"Calling service {self.service_url} Context {json.dumps(context)}")  
        response = await async_get_service_response(self.service_url, context)  
        return response  

    async def send_message(self, target_agent, message):  
        await target_agent.receive_message(message)  

    async def receive_message(self, message):  
        await self.message_queue.put(message)  

    async def process_messages(self):  
        while True:
            if self.message_queue.qsize() > 0:
                message = await self.message_queue.get()
                # Process the message
                self.message_queue.task_done()
            else:
                break 
