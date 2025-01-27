from datetime import datetime

from app.chat.chat_title_pipeline import ChatTitlePipeline
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

    async def create_chat(
            self,
            user_message: str,
    ) -> str:
        chat_name_pipeline = ChatTitlePipeline()
        response = await chat_name_pipeline.execute(message=user_message)
        chat_obj = Chat(title=response["title"])
        chat_obj.timestamp = datetime.now()
        return await self.mdb.add_entry(chat_obj)