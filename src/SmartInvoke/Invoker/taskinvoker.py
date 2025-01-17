from datetime import datetime  
import json  
import logging  
from typing import Any, Dict, Optional, Callable, Tuple, Union  
import aiofiles  
from pydantic import BaseModel, ValidationError  
from dataclasses import dataclass  
from common import (  
    BaseCacheWrapper, ChatSession, PluginLoader, AgentConfigLoader, ConfigurationError, Context, Task, Plan, PerformanceMonitor  
)  
from Config import AppConfig  
from common import CommandProcessor, CommandProcessorError, RequestData, UserAction
from common.functions import parse_responsejson, generate_cache_key
from common.openai_utils import OpenAIUtility
from userprofiles import UserProfile  
from agents import InteractiveAgent

class TaskExecutionError(Exception):  
    """Exception raised for errors in task execution."""  
    pass  

@dataclass  
class SmartInvokerConfig:  
    agents: Dict[str, Any]  
    retry: Optional[Dict[str, int]] = None  
    version: Optional[str] = None
    last_updated: Optional[str] = None
    cache: Optional[Dict[str, Any]] = None

class SmartInvoker:  
    def __init__(  
        self, config: SmartInvokerConfig, agents: Dict[str, Any], planner_prompt: str,   
        request_data: RequestData, cache: Optional[BaseCacheWrapper] = None,   
        command_prompt_path: Optional[str] = None, chat_session: Optional[ChatSession] = None,   
        openai_utility: Optional[OpenAIUtility] = None  
    ):  
        self.config = config  
        self.agents = agents  
        self.planner_prompt = planner_prompt  
        self.performance_monitor = PerformanceMonitor()  
        self.cache = cache  
        self.user_id = request_data.UserId  
        self.user_email = request_data.UserEmail  
        self.query = request_data.Query  
        self.request_id = request_data.RequestId  
        self.command_prompt_path = command_prompt_path  
        self.chat_session = chat_session  
        self.openai_utility = openai_utility  
        self.is_show_plan_only = request_data.IsShowPlanOnly  
        self.include_user_profile_attributes = False  # Consider passing this from app config or request data  

    @classmethod  
    async def create(  
        cls, request_data: RequestData, cache: BaseCacheWrapper, openai: OpenAIUtility,   
        chat_session: ChatSession, config_path: Optional[str] = None,   
        planner_prompt_file_path: Optional[str] = None, command_prompt_path: Optional[str] = None  
    ) -> 'SmartInvoker':  
        if not request_data.Query:  
            raise ValueError("Query is required")  

        config = await cls.load_config(config_path)  
        agents = await cls.load_agents(config)  
        planner_prompt = await cls.load_planner_prompt(planner_prompt_file_path)  

        return cls(config, agents, planner_prompt, request_data, cache, command_prompt_path, chat_session, openai)  

    @staticmethod  
    async def load_config(config_path: Optional[str]) -> SmartInvokerConfig:  
        try:  
            config_data = await AgentConfigLoader.load(config_path)  
            return SmartInvokerConfig(**config_data)  
        except (ConfigurationError, ValidationError) as e:  
            logging.error(f"Failed to load configuration: {e}")  
            raise  

    @staticmethod  
    async def load_planner_prompt(planner_prompt_path: str) -> str:  
        async with aiofiles.open(planner_prompt_path, 'r', encoding= 'utf-8') as prompt_file:  
            prompt = await prompt_file.read()  
        return prompt.strip()  

    @staticmethod  
    async def load_agents(config: SmartInvokerConfig) -> Dict[str, Any]:  
        agents = {}  
        retry_config = config.retry or {}  
        max_retries = retry_config.get('max_retries', 3)  
        backoff_factor = retry_config.get('backoff_factor', 2)  

        for agent_name, agent_info in config.agents.items():  
            agent_class = PluginLoader.load_class(agent_info['module'], agent_info['class'])  
            if 'service_url' in agent_info:  
                service_url=agent_info['service_url']
            else:
                service_url=None
            agents[agent_name] = agent_class(  
                agent_name, service_url, agent_info, max_retries, backoff_factor  
            )  
        return agents  

    async def resolve_dependencies(self, task: Task, completed_tasks: Dict[str, Any]) -> Union[Task, UserAction]:   
        """Resolve dependencies for the task using results from completed tasks."""  
        if not task.dependencies:  
            return task  

        for dependency_param, dependency_step in task.dependencies:  
            if dependency_step in completed_tasks:  
                prompt = (  
                    f"Your task is to identify the value of '{dependency_param}' from the below provided content. "  
                    f"Don't return any other information other than the value of '{dependency_param}'. "  
                    f"If you can't find the value of '{dependency_param}', please return 'not_found'."  
                )

                messages = [  
                    {"role": "system", "content": prompt},  
                    {"role": "user", "content": completed_tasks[dependency_step]}  
                ] 
                app_config = AppConfig.get_instance()
                try: 
                    result = await self.openai_utility.generate_completion(  
                        prompt=messages, gpt_deployment_name=app_config.GPT_DEPLOYMENT_NAME, conversation_id=self.request_id ,ai_assistant=app_config.MODULE_NAME,max_token=2048 , request_id = self.request_id
                    )  
                    if result == "not_found":  
                        raise TaskExecutionError(f"Dependency {dependency_param} not found in task {dependency_step}")  
                    task.agent_payload[dependency_param] = result 
                except Exception as e:  
                    logging.error(f"Error resolving dependencies for task {task.step}: {e}", exc_info=True)  
                    return UserAction(ActionType="UserMessage", Message=completed_tasks[dependency_step])  
        return task  

    async def delegate_task(self, task: Task, context: Context, status_callback: Callable[[str], None]) -> Any:  
        """Delegate the task to the appropriate agent."""  
        agent = self.agents.get(task.agent_name)  
        if not agent:  
            raise TaskExecutionError(f"Agent {task.agent_name} not found.")  

        status_callback(task.status_message)  
        if isinstance(agent, InteractiveAgent):  
            # Handle InteractiveAgent separately  
            message_type = context.get("MessageType")  
            if message_type is not None:  
                message_type = str(message_type).lower()  
                if message_type == "text":  
                    user_message = context.get("UserMessage")  
                    if not user_message:
                        raise ValueError("No UserMessage found in context")  
                    return user_message
                if message_type == "json":  
                    for key, value in context.__iter__():  
                        if "json" in key:  
                            user_message = value  
                            return user_message  

                
        cache_key = generate_cache_key(  
            user_id=self.user_id, user_query=f'{task.agent_name}{json.dumps(task.agent_payload)}',   
            is_permission_check_enabled=True  
        )  

        if self.cache:  
            cached_result = self.cache.read_from_cache(cache_key)  
            if cached_result:  
                status_callback(f"Using cached result for step {task.step}")  
                return cached_result  

        result = await agent.perform_task(context)  
        if not result:
            raise TaskExecutionError(f"We couldn't complete your request because the agent ({task.agent_name}) couldn't retrieve the necessary information in step {task.step}. Please try again or reach out for assistance.")
        if self.cache:  
            self.cache.write_to_cache(cache_key, result)  

        status_callback(f"Step {task.step} completed")  
        return result  

    async def generate_plan(self) -> Union[Plan, UserAction]:  
        """Generate the execution plan."""  
        plan = Plan()  

        if self.include_user_profile_attributes:  
            user_profile = UserProfile(self.user_id)  
            user_profile_attributes = await user_profile.get_user_profile_attributes()  
        
        prompt = (  
            f"{self.planner_prompt}\n"  
            f"\n################### \n"
            f"Current date is {datetime.now().strftime('%d %B %Y')}\n"  
            f"user Id is {self.user_id}\n"
            f"\n################### \n"
        )  

        for agent_name, details in self.config.agents.items():  
            agent_description = details.get("AgentDescription", "")  
            prompt += f"{agent_name}: {agent_description}\n"  
            request_template = details.get("request_template", {})  
            if request_template:  
                if isinstance(request_template, list):  
                    for template in request_template:  
                        for key, value in template.items():  
                            prompt += f"\t\t{key}: {value}\n"  
                else:  
                    for key, value in request_template.items():  
                        prompt += f"\t\t{key}: {value}\n"  
            prompt += "\n"  

        app_config = AppConfig.get_instance()  
        chat_session = ChatSession(  
            redis_host=app_config.REDIS_HOST, redis_password=app_config.REDIS_PASSWORD,   
            user_history_retrieval_limit=10  
        )  

        context_domain = chat_session.get_current_domain_context(self.user_id)  
        recent_chat_history = chat_session.get_user_history(self.user_id, context_domain)  

        if recent_chat_history:  
            prompt += f'\nAlso below is the recent chat history for the user:\n{recent_chat_history}\n'  

        messages = [  
            {"role": "system", "content": prompt},  
            {"role": "user", "content": self.query}  
        ]  

        result = await self.openai_utility.generate_completion(prompt= messages,gpt_deployment_name= app_config.GPT_DEPLOYMENT_NAME,ai_assistant=app_config.MODULE_NAME,conversation_id=self.request_id , request_id = self.request_id)  
        logging.info(result)
        try:
            json_data = parse_responsejson(result)  
        except Exception as e:
            if 'ActionType' not in result:
                return UserAction("clarificationNeeded",result)
            else:
                logging.info("Retrying with generate_completion_json_format due to missing ActionType.")
                result = await self.openai_utility.generate_completion_json_format(prompt= messages,
                                                            gpt_deployment_name= app_config.GPT_DEPLOYMENT_NAME,
                                                            ai_assistant=app_config.MODULE_NAME,
                                                            conversation_id=self.request_id, request_id = self.request_id )  
                try:
                    json_data = parse_responsejson(result)  
                except Exception as e:
                    raise TaskExecutionError("Error executing plan: {e}")
        if json_data is None:
            return UserAction("clarificationNeeded",result)
        
        if json_data.get("ActionType") == "Execute":  
            for item in json_data.get("ExecutePlan", []):  
                step = item["Step"]  
                agent_name = item["Agent name"]  
                agent_payload = item["Agent payload"]  
                status_message = item["Status Message"]  
                agent_payload['UserId'] = self.user_id  
                agent_payload['UserEmail'] = self.user_email
                agent_payload['OrigionalQuery']=self.query
                if self.include_user_profile_attributes and user_profile_attributes:  
                    agent_payload['UserProfileAttributes'] = json.dumps(user_profile_attributes)  
                if self.request_id:  
                    agent_payload['RequestId'] = self.request_id
                dependencies = [  
                    (dep["dependency_parameter"], dep["dependency_step"])   
                    for dep in item.get("dependency", [])  
                ]  

                task = Task(step, agent_name, agent_payload, status_message, dependencies)  
                plan.add_task(task)  

            logging.info(f"Generated plan: {plan}")  
            return plan  

        elif json_data.get("ActionType") in ("UserMessage", "ClarificationNeeded"):  
            return UserAction(**json_data)  

    async def execute_plan(self, plan: Plan, status_callback: Callable[[str], None]) -> Any:  
        """Execute the generated plan."""  
        context = Context()  
        context.set('query', 'test query')  
        completed_tasks = {} 
        combined_results = {}  
 

        for task in plan:  
            if task.is_ready(completed_tasks.keys()):  
                with self.performance_monitor.monitor(task):  
                    resolved_task = await self.resolve_dependencies(task, completed_tasks)  
                    if isinstance(resolved_task, UserAction):  
                        return resolved_task.Message
                    status_callback(f"🏃‍♂️ Executing Agent {resolved_task.agent_name} for step {resolved_task.step}")
                    result = await self.delegate_task(resolved_task, resolved_task.get_agent_payload(), status_callback)  
                    resolved_task.set_result(result)  
                    context.data['result'] = result  # Update context with the result of the task  
                    completed_tasks[resolved_task.step] = result
                    self.chat_session.append_to_user_history_system_message(self.user_id,"Task Execution Completed", f"Step {resolved_task.get_step()} - Task {resolved_task.agent_name} Complete.Task Execution Result: {result}")
                    logging.info(f"Step {resolved_task.get_step()} - Task {resolved_task.agent_name} .result: {result}") 
                    
                    if task.agent_name == "UserProxyAgent":
                        status_callback(f"invoking UserProxyAgent for step {resolved_task.step}")
                        return result 
                    # Combine results only for tasks without dependencies  
                    if not task.dependencies:  
                        combined_results[f'Step {resolved_task.step}:{resolved_task.status_message}'] = result  
                    

        self.performance_monitor.report()  
        if len(combined_results) > 1:  
            combined_results_str = json.dumps(combined_results, indent=2)  
            logging.info(f"Combined results of tasks without dependencies: {combined_results_str}")  
            combined_processed_result= await self.process_multi_step_result(combined_results_str)
            if combined_processed_result:
                return combined_processed_result
            else:
                first_key, first_value = list(combined_results.items())[0]  
                return first_value
        else:
            return context.data.get('result', "No data found")  

    async def review_session_history(self):  
        """Review the session history."""  
        pass  
    
    async def process_multi_step_result(self, result: Any): 

        """Process the multi-step result."""  
        try:
            app_config = AppConfig.get_instance()  

            prompt = (  
                        f"Your task is review the multi-step response to the question {self.query} from the below provided content. "  
                        f"Don't return any other information other than what is mentioned in the below content. "  
                        f"Your job is to combine these multi-step responses into a single, easy-to-read response."  
                        f"the output must be a JSON object that contains three attributes TextResponse and AssociatedImageLink and AssociatedVideoLink. do not incldue ```json and simply output the json object only. the output must be only a JSON object and nothing else."
                    )  
            messages = [  
                {"role": "system", "content": prompt},  
                {"role": "user", "content": result}  
            ] 

            logging.info("------------------------------------------") 
            
            finalresult = await self.openai_utility.generate_completion(prompt= messages,gpt_deployment_name= app_config.GPT_DEPLOYMENT_NAME,ai_assistant=app_config.MODULE_NAME,conversation_id=self.request_id , request_id = self.request_id)  
            logging.info(finalresult)
            if finalresult :
                return finalresult
            return None
        except Exception as e:
            logging.info(f"Error combining result from multi step- {e}")
            return None

    async def process_command(self):  
        """Process the command."""  
        command_processor = CommandProcessor(  
            request_id=self.request_id, user_id=self.user_id, user_request=self.query,   
            prompt_library_path=self.command_prompt_path, chat_session=self.chat_session,   
            openai_utility=self.openai_utility  
        )  
        return await command_processor.validate_and_extract_command()  

    async def handle_request(self, request: Any, status_callback: Callable[[str], None]) -> Tuple[str, str]:
        """Handle the incoming request."""  
        try:  
            app_config = AppConfig.get_instance()  

            if app_config.PROCESS_COMMANDS:  
                command_processing_result = await self.process_command()  
                if command_processing_result:  
                    return command_processing_result, None 
            status_callback ("🔄 Loading agents")
            execution_plan = await self.generate_plan()  
            status_callback("✅ Execution plan generated")
            self.chat_session.append_to_user_history_system_message(self.user_id,"Query Execution Plan Generated", str(execution_plan))
            if isinstance(execution_plan, UserAction):  
                return execution_plan.Message, None

            if self.is_show_plan_only:  
                return str(execution_plan),None  

            result = await self.execute_plan(execution_plan, status_callback)  
            agent_list =execution_plan.get_unique_agents()
            logging.info(f'agent_list - {agent_list}')
            return result ,agent_list

        except Exception as e:  
            #if error contains ResponsibleAIPolicyViolation, then log the error and return the error message
            logging.error(f"Error executing plan: {e}", exc_info=True)  
            if hasattr(e, 'code'):
                if e.code == 'content_filter':
                    return '''Your request couldn’t be processed because it was blocked by Azure OpenAI's content safety filter. Please modify your request and try again. If you believe this is an error, please contact support.'''
                elif e.code == 'DeploymentNotFound':
                    return '''It looks like the OpenAI deployment you're trying to access isn't available right now. If you just created it, it might take a few minutes to show up. Please wait a moment and try again.'''
                elif e.code == 'SecretNotFound':
                    return '''We are not able to fetch the secret from the key vault. Please check the secret name and try again.'''
                else:
                    raise TaskExecutionError(f"Error executing plan: {e}")
            elif 'Forbidden' in str(e):
                return '''your request couldn't be processed because we are Unable to retrieve a response from the service: Access restricted by IP address. Please contact support.'''
            elif isinstance(e, TaskExecutionError):
                return f"Error executing plan: {e}"
            else:
                raise TaskExecutionError("Error executing plan: {e}")