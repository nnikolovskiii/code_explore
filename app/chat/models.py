from datetime import datetime
from typing import Optional

from app.databases.mongo_db import MongoEntry


class Message(MongoEntry):
    role: str
    content: str
    order: int
    chat_id: str


class Chat(MongoEntry):
    title: str
    timestamp: datetime = datetime.now()
    num_messages: Optional[int] = 0


class ChatApi(MongoEntry):
    type: str
    api_key: str
    base_url: Optional[str] = None


class ChatModelConfig(MongoEntry):
    name: str
    chat_api_type: str
    active: Optional[bool] = False
