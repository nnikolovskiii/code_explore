import asyncio
from datetime import datetime
from app.databases.mongo_db import MongoEntry, MongoDBDatabase


class Message(MongoEntry):
    role: str
    content: str
    order: int
    chat_id: str


class Chat(MongoEntry):
    title: str
    timestamp: datetime = datetime.now()
