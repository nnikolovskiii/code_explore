import asyncio

from app.databases.mongo_db import MongoEntry, MongoDBDatabase


class Flag(MongoEntry):
    name: str
    active: bool

async def create_chat_rag_flag():
    mdb = MongoDBDatabase()
    await mdb.add_entry(Flag(name="chat_rag", active=True))

# asyncio.run(create_chat_rag_flag())