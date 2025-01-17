import json  
import os  
import logging  
import aiofiles  
import asyncio  
  
class ConfigurationError(Exception):  
    pass  
  
class AgentConfigLoader:  
    @staticmethod  
    async def load(config_path=None):  
        if config_path is not None:  
            return await AgentConfigLoader._load_from_file(config_path)  
        else:  
            return await AgentConfigLoader._load_from_cosmosdb()  
  
    @staticmethod  
    async def _load_from_file(config_path):  
        if not os.path.exists(config_path):  
            raise ConfigurationError(f"Configuration file {config_path} does not exist.")  
          
        async with aiofiles.open(config_path, 'r') as file:  
            config = json.loads(await file.read())  
          
        return await AgentConfigLoader._validate_config(config, config_path)  
  
    @staticmethod  
    async def _load_from_cosmosdb():  
        # Simulate async operation, replace this with actual async call to Cosmos DB  
        await asyncio.sleep(1)  
        raise ConfigurationError(f"Failed to query Cosmos DB for configuration.")  
  
    @staticmethod  
    async def _validate_config(config, source):  
        if 'agents' not in config:  
            raise ConfigurationError(f"Configuration from {source} is missing 'agents' key.")  
        if 'retry' not in config:  
            config['retry'] = {"max_retries": 3, "backoff_factor": 2}  
        if 'cache' not in config:  
            config['cache'] = {"enabled": False, "ttl": 300}  
        for agent_name, agent_info in config['agents'].items():  
            if 'module' not in agent_info or 'class' not in agent_info:  
                raise ConfigurationError(f"Agent '{agent_name}' in {source} is missing 'module' or 'class' key.")  
        logging.info(f"Configuration loaded from {source}")  
        return config  
