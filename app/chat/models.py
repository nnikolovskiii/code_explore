from datetime import datetime
from typing import Optional

from pydantic import EmailStr

from app.databases.mongo_db import MongoEntry


class Message(MongoEntry):
    role: str
    content: str
    order: int
    chat_id: str


class Chat(MongoEntry):
    user_email: Optional[str] = None
    title: str
    timestamp: datetime = datetime.now()
    num_messages: Optional[int] = 0


class ModelApi(MongoEntry):
    type: str
    api_key: str
    base_url: Optional[str] = None


class ModelConfig(MongoEntry):
    name: str
    chat_api_type: str
    active: Optional[bool] = False
    model_type: Optional[str] = None
