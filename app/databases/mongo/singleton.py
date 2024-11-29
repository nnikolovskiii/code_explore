from app.databases.mongo.db import MongoDBDatabase

mdb = None

async def get_db() -> MongoDBDatabase:
    global mdb
    if mdb is None:
        mdb = MongoDBDatabase()
    return mdb