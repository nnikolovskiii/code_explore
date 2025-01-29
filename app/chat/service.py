from typing import Tuple

from app.models.chat import ChatApi, ChatModelConfig, get_fernet
from app.chat.models import Message, Chat
from app.databases.mongo_db import MongoDBDatabase
from app.models.Flag import Flag


class ChatService:
    def __init__(self, mdb: MongoDBDatabase):
        self.mdb = mdb

    async def get_messages_from_chat(
            self,
            chat_id: str,
    ):
        user_messages = await self.mdb.get_entries(Message, doc_filter={"chat_id": chat_id, "role": "user"})
        assistant_messages = await self.mdb.get_entries(Message, doc_filter={"chat_id": chat_id, "role": "assistant"})

        user_messages = sorted(user_messages, key=lambda x: x.order)
        assistant_messages = sorted(assistant_messages, key=lambda x: x.order)

        return {"user_messages": user_messages, "assistant_messages": assistant_messages}

    async def get_history_from_chat(
            self,
            chat_id: str,
    ):
        history = []
        history_flag = await self.mdb.get_entry_from_col_value(
            column_name="name",
            column_value="history",
            class_type=Flag
        )

        if history_flag.active and chat_id is not None:
            messages = await self.get_messages_from_chat(chat_id=chat_id)
            user_messages = messages["user_messages"]
            assistant_messages = messages["assistant_messages"]

            for i in range(len(user_messages)):
                history.append({"role": "user", "content": user_messages[i].content})
                if i < len(assistant_messages):
                    history.append({"role": "user", "content": assistant_messages[i].content})

        return history

    async def get_active_chat_model(self) -> ChatModelConfig:
        chat_model = await self.mdb.get_entry_from_col_value(
            column_name="active",
            column_value=True,
            class_type=ChatModelConfig,
        )

        return chat_model

    async def get_chat_api(self, type: str) -> ChatApi:
        chat_api = await self.mdb.get_entry_from_col_value(
            column_name="type",
            column_value=type,
            class_type=ChatApi,
        )
        encrypted_bytes = chat_api.api_key.encode('utf-8')
        chat_api.api_key = get_fernet().decrypt(encrypted_bytes).decode()
        return chat_api


    async def get_model_and_api(self, model_name) -> Tuple[ChatApi, ChatModelConfig]:
        chat_model = await self.mdb.get_entry_from_col_values(
            columns={"name": model_name},
            class_type=ChatModelConfig,
        )

        chat_api = await self.get_chat_api(chat_model.chat_api_type)

        if chat_model is None or chat_api is None:
            raise Exception(f"Model {model_name} not found")

        return chat_api, chat_model