from typing import Optional

from bson import ObjectId
from app.databases.mongo_db import MongoEntry, MongoDBDatabase


class SimpleProcess(MongoEntry):
    finished: bool = False
    process_type: str
    url: str
    type: str
    order: int
    status: Optional[str] = None

async def create_simple_process(
        url: str,
        process_type: str,
        type: str,
        order: int,
        mdb:MongoDBDatabase
)->SimpleProcess:
    process_id = await mdb.add_entry(SimpleProcess(
        process_type=process_type,
        url=url,
        type=type,
        order=order
    ))
    return await mdb.get_entry(ObjectId(process_id), SimpleProcess)


async def finish_simple_process(
        process:SimpleProcess,
        mdb:MongoDBDatabase
):
    process.finished = True
    await mdb.update_entry(process)

async def update_status_process(
        new_status: str,
        process:SimpleProcess,
        mdb:MongoDBDatabase
):
    process.status = new_status
    await mdb.update_entry(process)