import os
from typing import Optional

from cryptography.fernet import Fernet
from pydantic import field_validator

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


class ChatModel(MongoEntry):
    name: str
    chat_api_type: str
    active: Optional[bool] = False

async def get_active_chat_model(mdb:MongoDBDatabase) -> ChatModel:
    chat_model = await mdb.get_entry_from_col_value(
        column_name="active",
        column_value=True,
        class_type=ChatModel,
    )

    return chat_model

async def get_chat_api(type:str, mdb: MongoDBDatabase) -> ChatApi:
    chat_api = await mdb.get_entry_from_col_value(
        column_name="type",
        column_value=type,
        class_type=ChatApi,
    )

    return ChatApi(id=chat_api.id,type=type, api_key=get_fernet().decrypt(chat_api.api_key).decode())
