from bson import ObjectId
from app.databases.mongo_db import MongoEntry, MongoDBDatabase


class SimpleProcess(MongoEntry):
    finished: bool = False
    process_type: str
    url: str
    type: str

async def create_simple_process(
        url: str,
        process_type: str,
        type: str,
        mdb:MongoDBDatabase
)->SimpleProcess:
    process_id = await mdb.add_entry(SimpleProcess(
        process_type=process_type,
        url=url,
        type=type
    ))
    return await mdb.get_entry(ObjectId(process_id), SimpleProcess)


async def finish_simple_process(
        process:SimpleProcess,
        mdb:MongoDBDatabase
):
    process.finished = True
    await mdb.update_entry(process)