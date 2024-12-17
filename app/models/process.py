from bson import ObjectId

from app.databases.mongo_db import MongoEntry, MongoDBDatabase


class Process(MongoEntry):
    finished: bool = False
    end: int
    curr: int = 0
    process_type: str
    url: str
    type: str

async def create_process(
        url: str,
        process_type: str,
        end:int,
        type: str,
        mdb:MongoDBDatabase
)->Process:
    process_id = await mdb.add_entry(Process(
        end=end,
        process_type=process_type,
        url=url,
        type=type
    ))
    return await mdb.get_entry(ObjectId(process_id), Process)

async def increment_process(
        process:Process,
        mdb:MongoDBDatabase,
        num: int
):
    process.curr = num
    await mdb.update_entry(process)

async def finish_process(
        process:Process,
        mdb:MongoDBDatabase
):
    process.finished = True
    await mdb.update_entry(process)