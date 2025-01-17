import pytest
import time
import logging
from contextlib import contextmanager
from unittest.mock import patch, MagicMock
from tabulate import tabulate
from common.task import Task
from common.performance_monitor import PerformanceMonitor, TaskNotEndedError 

@pytest.fixture
def mock_time():
    with patch('common.performance_monitor.time.time') as mock_time:
        yield mock_time

@pytest.fixture
def mock_logging():
    with patch('common.performance_monitor.logging') as mock_logging:
        yield mock_logging

@pytest.fixture
def task():
    return Task(agent_name="test_agent", step=1, agent_payload=[])

@pytest.fixture
def performance_monitor():
    return PerformanceMonitor()

def test_start(performance_monitor, task, mock_time):
    mock_time.return_value = 123.456
    performance_monitor.start(task)
    assert performance_monitor.start_times[task.agent_name] == 123.456

def test_end(performance_monitor, task, mock_time):
    mock_time.side_effect = [123.456, 789.012]
    performance_monitor.start(task)
    performance_monitor.end(task)
    assert performance_monitor.end_times[task.agent_name] == 789.012

def test_end_task_not_started(performance_monitor, task):
    with pytest.raises(TaskNotEndedError, match="Task test_agent was not started."):
        performance_monitor.end(task)

def test_report(performance_monitor, task, mock_time, mock_logging):
    mock_time.side_effect = [123.456, 789.012]
    performance_monitor.start(task)
    performance_monitor.end(task)
    performance_monitor.report()
    expected_table = tabulate([["test_agent", "665.56 seconds"]], headers=["Agent Name", "Duration"], tablefmt="grid")
    mock_logging.info.assert_called_with("\n\n" + expected_table + "\n\n")

def test_report_task_not_ended(performance_monitor, task, mock_time, mock_logging):
    mock_time.return_value = 123.456
    performance_monitor.start(task)
    performance_monitor.report()
    expected_table = tabulate([["test_agent", "Not ended"]], headers=["Agent Name", "Duration"], tablefmt="grid")
    mock_logging.info.assert_called_with("\n\n" + expected_table + "\n\n")

def test_str(performance_monitor, task, mock_time):
    mock_time.side_effect = [123.456, 789.012]
    performance_monitor.start(task)
    performance_monitor.end(task)
    report_str = str(performance_monitor)
    assert report_str == "Performance Report:\nTask test_agent took 665.56 seconds"

def test_str_task_not_ended(performance_monitor, task, mock_time):
    mock_time.return_value = 123.456
    performance_monitor.start(task)
    report_str = str(performance_monitor)
    assert report_str == "Performance Report:\nTask test_agent has not ended."