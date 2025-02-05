from typing import Optional

from bson import ObjectId

from app.container import container
from app.databases.mongo_db import MongoEntry, MongoDBDatabase


class ProcessTracker(MongoEntry):
    finished: bool = False
    end: Optional[int] = None
    curr: Optional[int] = None
    status: Optional[str] = ""
    process_type: str
    url: str
    type: str
    order: Optional[int] = None
    group: Optional[str] = None


class ProgressCoordinator:
    mdb: MongoDBDatabase
    tracker: ProcessTracker

    def __init__(self, mdb: MongoDBDatabase, tracker: ProcessTracker):
        self.mdb = mdb
        self.tracker = tracker

    @classmethod
    async def create(
            cls,
            url: str,
            process_type: str,
            type: str,
            mdb: MongoDBDatabase,
            order: Optional[int] = None,
            end: Optional[int] = None,
            curr: Optional[int] = None,
            status: Optional[str] = None,
            group: Optional[str] = None,
    ) -> "ProgressCoordinator":
        if end is not None and end == 0:
            raise Exception("End cannot be 0.")

        tracker = ProcessTracker(
            end=end,
            process_type=process_type,
            url=url,
            type=type,
            order=order,
            curr=curr,
            status=status,
            group=group,
        )

        process_id = await mdb.add_entry(tracker)
        new_tracker = await mdb.get_entry(ObjectId(process_id), ProcessTracker)
        return cls(mdb, new_tracker)

    async def increment_progress(self, num: int, step: int = 10) -> None:
        if self.tracker.finished:
            raise ValueError("Cannot update progress on finished process")

        if num % step == 0:
            updated = await self.mdb.atomic_update(
                ObjectId(self.tracker.id),
                {"$set": {"curr": num}},
                ProcessTracker
            )
            if updated:
                self.tracker.curr = num

    async def set_total_steps(self, end: int) -> None:
        if end < 1:
            raise ValueError("Total steps must be positive")

        updated = await self.mdb.atomic_update(
            ObjectId(self.tracker.id),
            {"$set": {"end": end, "curr": 0}},
            ProcessTracker
        )
        if updated:
            self.tracker.end = end
            self.tracker.curr = 0

    async def update_status(self, new_status: str) -> None:
        updated = await self.mdb.atomic_update(
            ObjectId(self.tracker.id),
            {"$set": {"status": new_status}},
            ProcessTracker
        )
        if updated:
            self.tracker.status = new_status

    async def complete_process(self) -> None:
        updated = await self.mdb.atomic_update(
            ObjectId(self.tracker.id),
            {"$set": {
                "finished": True,
                "curr": self.tracker.end,
                "status": "completed"
            }},
            ProcessTracker
        )
        if updated:
            self.tracker.finished = True
            self.tracker.curr = self.tracker.end
            self.tracker.status = "completed"

        telegram_bot = container.telegram_bot()
        await telegram_bot.send_message(
            f"✅ *{self.tracker.type.title()} Process Completed* \n"
            f"• *Type:* `{self.tracker.process_type}`\n"
            f"• *URL:* `{self.tracker.url}`\n"
            f"• *Status:* `{'Completed successfully' if self.tracker.curr == self.tracker.end else 'Partial completion'}`\n"
            f"{f'• *Group:* `{self.tracker.group}`\n' if self.tracker.group else ''}"
            f"\\#progress \\#{self.tracker.type.lower()}",
            chat_id=5910334398
        )

    async def refresh_state(self) -> None:
        self.tracker = await self.mdb.get_entry(
            ObjectId(self.tracker.id),
            ProcessTracker
        )