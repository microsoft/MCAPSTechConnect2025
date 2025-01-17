import time
import logging
from contextlib import contextmanager

from tabulate import tabulate
from .task import Task
class TaskNotEndedError(Exception):
    pass

class PerformanceMonitor:
    def __init__(self):
        self.start_times = {}
        self.end_times = {}

    @contextmanager
    def monitor(self, task: Task):
        self.start(task)
        try:
            yield
        finally:
            self.end(task)

    def start(self, task: Task):
        self.start_times[task.agent_name] = time.time()

    def end(self, task: Task):
        if task.agent_name not in self.start_times:
            raise TaskNotEndedError(f"Task {task.agent_name} was not started.")
        self.end_times[task.agent_name] = time.time()

    def report(self):
        report_data = []  
        for agent_name, start_time in self.start_times.items():  
            end_time = self.end_times.get(agent_name)  
            if end_time:  
                duration = end_time - start_time  
                report_data.append([agent_name, f"{duration:.2f} seconds"])  
            else:  
                report_data.append([agent_name, "Not ended"])  
          
        table = tabulate(report_data, headers=["Agent Name", "Duration"], tablefmt="grid")  
        logging.info("\n\n" + table +"\n\n")  

    def __str__(self):
        report_lines = ["Performance Report:"]
        for agent_name, start_time in self.start_times.items():
            end_time = self.end_times.get(agent_name)
            if end_time:
                duration = end_time - start_time
                report_lines.append(f"Task {agent_name} took {duration:.2f} seconds")
            else:
                report_lines.append(f"Task {agent_name} has not ended.")
        return "\n".join(report_lines)

