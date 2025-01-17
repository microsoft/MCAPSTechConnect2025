import logging  
from typing import List  
from .task import Task  
  
class PlanError(Exception):  
    """Custom exception for Plan-related errors."""  
    pass  
  
class Plan:  
    __slots__ = ['_tasks']  
  
    def __init__(self):  
        self._tasks: List[Task] = []  
  
    @property  
    def get_tasks(self) -> List[Task]:  
        """Get the list of tasks."""  
        return self._tasks  
  
    def add_task(self, task: Task) -> None:  
        """Add a task to the plan."""  
        if isinstance(task, Task):  
            self._tasks.append(task)  
        else:  
            raise TypeError("Expected a Task instance")  
  
    def get_independent_tasks(self) -> List[Task]:  
        """Return tasks without dependencies."""  
        return [task for task in self._tasks if not task.dependencies]  
  
    def get_dependent_tasks(self, completed_task: Task) -> List[Task]:  
        """Return tasks that depend on the completed task."""  
        return [task for task in self._tasks if completed_task.agent_name in task.dependencies]  
  
    def adjust_plan(self, completed_task):  
        # Logic to adjust the plan based on the completed task  
        # For example, you might want to reprioritize tasks or add new tasks based on the outcome  
        pass  
  
    def __str__(self) -> str:  
        """Return a string representation of the plan."""  
        task_descriptions = '\n'.join(str(task) for task in self._tasks)  
        return f"Plan with tasks:\n\n{task_descriptions}"  
  
    def __enter__(self):  
        """Enter the runtime context related to this object."""  
        return self  
  
    def __exit__(self, exc_type, exc_val, exc_tb):  
        """Exit the runtime context related to this object."""  
        if exc_type:  
            logging.info(f"An exception occurred: {exc_val}")  
  
    def __iter__(self):  
        """Return an iterator over the tasks."""  
        return iter(self._tasks)  
    
    def get_unique_agents(self) -> str:
        """Get a comma-separated string of unique agents based on the tasks in the plan."""
        # Use a set to avoid duplicates, then join the set into a comma-separated string.
        return ', '.join(sorted({task.agent_name for task in self._tasks}))