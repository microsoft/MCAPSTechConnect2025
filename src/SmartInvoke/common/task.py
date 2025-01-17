from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class Task:
    step: int
    agent_name: str
    agent_payload: Dict[str, Any]
    status_message: str = ""
    dependencies: List[Tuple[str, int]] = field(default_factory=list)
    result: Optional[Any] = None

    def get_agent_name(self) -> str:
        return self.agent_name

    def get_agent_payload(self) -> Dict[str, Any]:
        return self.agent_payload

    def get_dependencies(self) -> List[Tuple[str, int]]:
        return self.dependencies

    def set_result(self, result: Any) -> None:
        self.result = result

    def get_step(self) -> int:
        return self.step

    def get_result(self) -> Optional[Any]:
        return self.result

    def is_ready(self, completed_tasks: Dict[int, 'Task']) -> bool:
        return all(dep[1] in completed_tasks for dep in self.dependencies)

    def __repr__(self) -> str:
        return (f"Task(step={self.step}, agent_name={self.agent_name}, "
                f"dependencies={self.dependencies}, result={self.result})")

    def __str__(self) -> str:
        dependencies = ', '.join([f"{dep[0]}: {dep[1]}" for dep in self.dependencies])
        return (f"\nTask(step={self.step}, agent_name={self.agent_name}, "
                f"agent_payload={self.agent_payload}, dependencies=[{dependencies}], "
                f"result={self.result})")
