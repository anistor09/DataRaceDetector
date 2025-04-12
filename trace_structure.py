from typing import List,Optional
from dataclasses import dataclass

@dataclass
class ThreadAction:
    id: int
    thread_id: int
    action_type: str
    memory_order: str
    location: str
    value: str
    read_from: Optional[int] = None

    def __str__(self):
        rf_part = f", read_from={self.read_from}" if self.read_from is not None else ""
        return (f"ThreadAction(id={self.id}, thread_id={self.thread_id}, "
                f"action_type='{self.action_type}', memory_order='{self.memory_order}', "
                f"location='{self.location}', value='{self.value}'{rf_part})")

@dataclass
class TraceStruct:
    trace_number:int
    actions:List[List[ThreadAction]]

    def __str__(self):
        result = [f"Trace #{self.trace_number}:"]
        for i, group in enumerate(self.actions):
            result.append(f"  Group {i + 1}:")
            for action in group:
                result.append(f"    {action}")
        return "\n".join(result)