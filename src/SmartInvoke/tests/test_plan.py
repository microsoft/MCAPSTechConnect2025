import pytest
import logging
from unittest.mock import MagicMock
from common.task import Task  
from common.plan import Plan, PlanError  

@pytest.fixture
def task():
    return Task(agent_name="test_agent", step="test_step", agent_payload="test_payload")

@pytest.fixture
def dependent_task():
    task = Task(agent_name="dependent_agent", step="test_step", agent_payload="test_payload")
    task.dependencies = ["test_agent"]
    return task

@pytest.fixture
def plan():
    return Plan()

def test_add_task(plan, task):
    plan.add_task(task)
    assert task in plan.get_tasks

def test_add_task_invalid_type(plan):
    with pytest.raises(TypeError, match="Expected a Task instance"):
        plan.add_task("not_a_task")

def test_get_independent_tasks(plan, task, dependent_task):
    plan.add_task(task)
    plan.add_task(dependent_task)
    independent_tasks = plan.get_independent_tasks()
    assert task in independent_tasks
    assert dependent_task not in independent_tasks

def test_get_dependent_tasks(plan, task, dependent_task):
    plan.add_task(task)
    plan.add_task(dependent_task)
    dependent_tasks = plan.get_dependent_tasks(task)
    assert dependent_task in dependent_tasks
    assert task not in dependent_tasks

def test_adjust_plan(plan, task):
    # This test is a placeholder since adjust_plan is not implemented
    plan.adjust_plan(task)
    # Add assertions here when adjust_plan is implemented

def test_str(plan, task):
    plan.add_task(task)
    plan_str = str(plan)
    assert plan_str == f"Plan with tasks:\n\n{str(task)}"

def test_enter_exit(plan):
    with plan as p:
        assert p is plan

def test_iter(plan, task):
    plan.add_task(task)
    tasks = list(iter(plan))
    assert task in tasks