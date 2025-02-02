from abc import ABC, abstractmethod
from typing import Dict, Any

from app.databases.mongo_db import MongoDBDatabase
from app.docs_process.group_process import GroupProcess
from app.models.docs import Link
from app.models.process_tracker import ProcessTracker, create_process


class SingleProcess(GroupProcess, ABC):
    order: int

    def __init__(self, mdb: MongoDBDatabase, group_id: str, order: int):
        super().__init__(mdb, group_id, Link)
        self.order = order

    async def add_not_processed(self, link_obj: Link) -> int:
        pass

    async def create_process_status(self) -> ProcessTracker | None:
        doc_filter = {"base_url": self.group_id}
        doc_filter.update(self.stream_filters)
        num_links = await self.mdb.count_entries(Link, doc_filter)
        process = await create_process(
            url=self.group_id,
            mdb=self.mdb,
            process_type=self.process_name,
            type="docs",
            order=self.order,
            group=self.process_type,
            curr=0,
            end=num_links,
        )
        return process

    @property
    def stream_filters(self) -> Dict[str, Any]:
        return {self.process_name: False}

    @property
    def execute_process_filters(self) -> Dict[str, Any]:
        return {self.process_name: False, "base_url": self.group_id}

