from abc import ABC, abstractmethod
from typing import TypeVar, Type, Dict, Any, Optional

from pydantic import BaseModel

from app.databases.mongo_db import MongoDBDatabase
from app.docs_process.process import Process
from app.models.docs import Link
from app.models.process_tracker import ProcessTracker, create_process, finish_process, increment_process

T = TypeVar('T', bound=BaseModel)


class GroupProcess(Process, ABC):
    class_type:Type[T]

    def __init__(self, mdb: MongoDBDatabase, group_id: str, class_type: Type[T]):
        super().__init__(mdb, group_id)
        self.class_type = class_type

    async def create_process_status(self) -> ProcessTracker | None:
        count = 0
        await self.mdb.delete_entries(
            class_type=self.class_type,
            doc_filter={"url": self.group_id})

        doc_filter = {"base_url": self.group_id}
        doc_filter.update(self.stream_filters)

        async for link_obj in self.mdb.stream_entries(
                class_type=Link,
                doc_filter=doc_filter,
        ):
            count += await self.add_not_processed(link_obj)

        if count > 0:
            return await create_process(
                url=self.group_id,
                end=count,
                curr=0,
                process_type=self.process_name,
                mdb=self.mdb,
                type="docs",
                group=self.process_type,
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
                doc_filter=self.execute_process_filters
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

    @property
    @abstractmethod
    def stream_filters(self) -> Dict[str, Any]:
        """Return the process_name."""
        pass

    @property
    @abstractmethod
    def execute_process_filters(self) -> Dict[str, Any]:
        """Return the process_name."""
        pass
