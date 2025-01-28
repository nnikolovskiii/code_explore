import os
from typing import Optional

from cryptography.fernet import Fernet

from app.databases.mongo_db import MongoEntry, MongoDBDatabase
from dotenv import load_dotenv

fernet = None


def get_fernet():
    global fernet
    if fernet is None:
        load_dotenv()
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is not set.")

        fernet = Fernet(encryption_key)
    return fernet


class ChatApi(MongoEntry):
    type: str
    api_key: str
    base_url: Optional[str] = None


class ChatModel(MongoEntry):
    name: str
    chat_api_type: str
    active: Optional[bool] = False
