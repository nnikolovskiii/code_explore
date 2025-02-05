from abc import ABC, abstractmethod
from typing import TypeVar, Type, Optional

from pydantic import BaseModel

from app.databases.mongo_db import MongoDBDatabase
from app.models.process_tracker import ProcessTracker, ProgressCoordinator

T = TypeVar('T', bound=BaseModel)


class Process(ABC):
    mdb: MongoDBDatabase
    group_id: str
    order:int
    progress_coordinator: Optional[ProgressCoordinator] = None

    def __init__(self, mdb: MongoDBDatabase, group_id: str, order: int):
        self.mdb = mdb
        self.group_id = group_id
        self.order = order

    @property
    @abstractmethod
    def process_name(self) -> str:
        """Return the process_name."""
        pass

    @property
    @abstractmethod
    def process_type(self) -> str:
        """Return the process_type."""
        pass

    @abstractmethod
    async def create_process_tracker(self) -> ProcessTracker | None:
        pass

    @abstractmethod
    async def execute_process(self):
        pass

    async def pre_execute_process(self):
        pass

    async def post_execute_process(self):
        pass
