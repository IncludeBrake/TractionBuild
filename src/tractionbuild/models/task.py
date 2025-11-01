from pydantic import BaseModel

class Task(BaseModel):
    id: str

class TaskStatus(BaseModel):
    pass

class TaskPriority(BaseModel):
    pass

__all__ = ["Task", "TaskStatus", "TaskPriority"]