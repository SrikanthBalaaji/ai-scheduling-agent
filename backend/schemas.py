from pydantic import BaseModel
from typing import List

class Event(BaseModel):
    id: str
    title: str
    date: str
    start_time: str
    end_time: str
    tags: List[str]
    description: str = ""
    campus: str = "Main"