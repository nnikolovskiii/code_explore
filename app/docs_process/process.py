from abc import ABC, abstractmethod
from typing import TypeVar, Type

from pydantic import BaseModel

from app.databases.mongo_db import MongoDBDatabase
from app.models.docs import Link
from app.models.process_tracker import ProcessTracker, create_process, finish_process, increment_process

T = TypeVar('T', bound=BaseModel)


class Process(ABC):
    mdb: MongoDBDatabase
    class_type: Type[T]
    group_id: str

    def __init__(self, mdb: MongoDBDatabase, class_type: Type[T], group_id: str):
        self.mdb = mdb
        self.class_type = class_type
        self.group_id = group_id

    @property
    @abstractmethod
    def process_type(self) -> str:
        """Return the process_type."""
        pass

    async def create_process_status(self) -> ProcessTracker | None:
        count = 0
        await self.mdb.delete_entries(
            class_type=self.class_type,
            doc_filter={"url": self.group_id})

        async for link_obj in self.mdb.stream_entries(
                class_type=Link,
                doc_filter={"base_url": self.group_id, "processed": False, "active": True},
        ):
            count += await self.add_not_processed(link_obj)

        if count > 0:
            return await create_process(
                url=self.group_id,
                end=count,
                curr=0,
                process_type=self.process_type,
                mdb=self.mdb,
                type="docs",
                group="post"
            )

        return None

    async def execute_process(self):
        await self.pre_execute_process()
        process = await self.create_process_status()

        if process is None:
            return

        count = 0
        async for entry in self.mdb.stream_entries(
                class_type=self.class_type,
                doc_filter={"url": self.group_id}
        ):
            await increment_process(process, self.mdb, count, 10)
            await self.execute_single(entry)
            count += 1

        await finish_process(process, self.mdb)

        await self.mdb.delete_entries(
            class_type=self.class_type,
            doc_filter={"url": self.group_id})

        await self.post_execute_process()

    async def pre_execute_process(self):
        pass

    async def post_execute_process(self):
        pass

    @abstractmethod
    async def execute_single(self, entry: T):
        pass

    @abstractmethod
    async def add_not_processed(self, link_obj: Link) -> int:
        pass
