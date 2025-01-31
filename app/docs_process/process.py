from abc import ABC, abstractmethod

from app.models.processstatus import ProcessStatus


class Process(ABC):
    @abstractmethod
    async def create_process_status(self, **kwargs) -> ProcessStatus | None:
        pass

    async def execute_process(self, **kwargs):
        process = await self.create_process_status(**kwargs)
