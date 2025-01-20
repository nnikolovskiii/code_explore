from typing import Optional

from bson import ObjectId

from app.databases.mongo_db import MongoEntry, MongoDBDatabase


class Process(MongoEntry):
    finished: bool = False
    end: Optional[int] = None
    curr: Optional[int] = None
    status: Optional[str] = ""
    process_type: str
    url: str
    type: str
    order: Optional[int] = None
    group: Optional[str] = None


async def create_process(
        url: str,
        process_type: str,
        type: str,
        mdb:MongoDBDatabase,
        order: Optional[int] = None,
        end: Optional[int] = None,
        curr: Optional[int] = None,
        status: Optional[str] = None,
        group: Optional[str] = None,
)->Process:
    process_id = await mdb.add_entry(Process(
        end=end,
        process_type=process_type,
        url=url,
        type=type,
        order=order,
        curr=curr,
        status=status,
        group=group,
    ))
    return await mdb.get_entry(ObjectId(process_id), Process)

async def increment_process(
        process:Process,
        mdb:MongoDBDatabase,
        num: int,
        step:int = 10,
):
    if num % step == 0:
        process.curr = num
        await mdb.update_entry(process)

async def set_end(
        process:Process,
        end: int,
        mdb:MongoDBDatabase,
):
    process.end = end
    process.curr = 0
    await mdb.update_entry(process)

async def update_status_process(
        new_status: str,
        process:Process,
        mdb:MongoDBDatabase
):
    process.status = new_status
    await mdb.update_entry(process)

async def finish_process(
        process:Process,
        mdb:MongoDBDatabase
):
    process.finished = True
    process.curr = process.end
    await mdb.update_entry(process)