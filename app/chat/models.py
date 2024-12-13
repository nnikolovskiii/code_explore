import asyncio
from datetime import datetime
from app.databases.mongo_db import MongoEntry, MongoDBDatabase


class Message(MongoEntry):
    role: str
    content: str
    timestamp: datetime = datetime.now()
    chat_id: str


class Chat(MongoEntry):
    pass