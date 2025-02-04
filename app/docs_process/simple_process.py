from abc import ABC, abstractmethod

from app.docs_process.process import Process
from app.models.docs import Link
from app.models.process_tracker import ProcessTracker, create_process, increment_process, finish_process


class SimpleProcess(Process, ABC):
    async def create_process_tracker(self) -> ProcessTracker | None:
        doc_filter = {"base_url": self.group_id}
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


    async def execute_process(self):
        await self.pre_execute_process()
        process = await self.create_process_tracker()

        if process is None:
            return

        count = 0
        async for entry in self.mdb.stream_entries(
                class_type=Link,
                doc_filter={"base_url": self.group_id}
        ):
            await increment_process(process, self.mdb, count, 10)
            await self.execute_single(entry)
            count += 1

        await finish_process(process, self.mdb)

        await self.post_execute_process()

    @abstractmethod
    async def execute_single(self, link_obj: Link):
        pass