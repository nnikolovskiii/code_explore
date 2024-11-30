from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase

mdb = None

async def get_mongo_db() -> MongoDBDatabase:
    global mdb
    if mdb is None:
        mdb = MongoDBDatabase()
    return mdb

qdb = None

async def get_qdrant_db() -> QdrantDatabase:
    global qdb
    if qdb is None:
        qdb = QdrantDatabase()
    return qdb