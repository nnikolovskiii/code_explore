from abc import ABC, abstractmethod
from typing import TypeVar, Type

from pydantic import BaseModel

from app.databases.mongo_db import MongoDBDatabase
from app.models.docs import Link
from app.models.process_tracker import ProcessTracker, create_process, finish_process, increment_process

T = TypeVar('T', bound=BaseModel)


class Process(ABC):
    mdb: MongoDBDatabase

    def __init__(self, mdb: MongoDBDatabase):
        self.mdb = mdb

    @property
    @abstractmethod
    def process_type(self) -> str:
        """Return the process_type."""
        pass

    async def create_process_status(self, class_type: Type[T], group: str) -> ProcessTracker | None:
        count = 0
        await self.mdb.delete_entries(
            class_type=class_type,
            doc_filter={"url": group})

        async for link_obj in self.mdb.stream_entries(
                class_type=Link,
                doc_filter={"base_url": group, "processed": False, "active": True},
        ):
            count += await self.add_not_processed(link_obj, class_type)

        if count > 0:
            return await create_process(
                url=group,
                end=count,
                curr=0,
                process_type=self.process_type,
                mdb=self.mdb,
                type="docs",
                group="post"
            )

        return None

    async def execute_process(self, class_type: Type[T], group: str):
        process = await self.create_process_status(class_type=class_type, group=group)

        if process is None:
            return

        count = 0
        async for entry in self.mdb.stream_entries(
                class_type=class_type,
                doc_filter={"url": group}
        ):
            await increment_process(process, self.mdb, count, 10)
            await self.execute_single(entry)
            count += 1

        await finish_process(process, self.mdb)

        await self.mdb.delete_entries(
            class_type=class_type,
            doc_filter={"url": group})

    @abstractmethod
    async def execute_single(self, entry: T):
        pass

    @abstractmethod
    async def add_not_processed(self, link_obj: Link, class_type: Type[T]) -> int:
        pass
