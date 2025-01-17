import pytest
from typing import Any, Dict, List, Optional, Tuple
from common.task import Task  # Replace 'common.task' with the actual module name

@pytest.fixture
def task():
    return Task(step=1, agent_name="test_agent", agent_payload={"key": "value"})

def test_get_agent_name(task):
    assert task.get_agent_name() == "test_agent"

def test_get_agent_payload(task):
    assert task.get_agent_payload() == {"key": "value"}

def test_get_dependencies(task):
    assert task.get_dependencies() == []

def test_set_result(task):
    task.set_result("test_result")
    assert task.result == "test_result"

def test_get_step(task):
    assert task.get_step() == 1

def test_get_result(task):
    task.set_result("test_result")
    assert task.get_result() == "test_result"

def test_is_ready_no_dependencies(task):
    completed_tasks = {}
    assert task.is_ready(completed_tasks) is True

def test_is_ready_with_dependencies(task):
    task.dependencies = [("dep_agent", 2)]
    completed_tasks = {2: Task(step=2, agent_name="dep_agent", agent_payload={})}
    assert task.is_ready(completed_tasks) is True

def test_is_ready_with_missing_dependencies(task):
    task.dependencies = [("dep_agent", 2)]
    completed_tasks = {}
    assert task.is_ready(completed_tasks) is False

def test_repr(task):
    assert repr(task) == "Task(step=1, agent_name=test_agent, dependencies=[], result=None)"

def test_str(task):
    assert str(task) == "\nTask(step=1, agent_name=test_agent, agent_payload={'key': 'value'}, dependencies=[], result=None)"