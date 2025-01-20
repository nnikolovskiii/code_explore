from app.chat.create_chat_name import create_chat_name
from app.chat.models import Message, Chat
from app.databases.mongo_db import MongoDBDatabase
from app.models.Flag import Flag


async def get_messages_from_chat(
        chat_id: str,
        mdb: MongoDBDatabase
):
    user_messages = await mdb.get_entries(Message, doc_filter={"chat_id": chat_id, "role": "user"})
    assistant_messages = await mdb.get_entries(Message, doc_filter={"chat_id": chat_id, "role": "assistant"})

    user_messages = sorted(user_messages, key=lambda x: x.order)
    assistant_messages = sorted(assistant_messages, key=lambda x: x.order)

    return {"user_messages": user_messages, "assistant_messages": assistant_messages}


async def get_history_from_chat(
        chat_id: str,
        mdb: MongoDBDatabase
):
    history = []
    history_flag = await mdb.get_entry_from_col_value(
        column_name="name",
        column_value="history",
        class_type=Flag
    )

    if history_flag.active and chat_id is not None:
        messages = await get_messages_from_chat(chat_id=chat_id, mdb=mdb)
        user_messages = messages["user_messages"]
        assistant_messages = messages["assistant_messages"]

        for i in range(len(user_messages)):
            history.append({"role": "user", "content": user_messages[i].content})
            if i < len(assistant_messages):
                history.append({"role": "user", "content": assistant_messages[i].content})

    return history

async def create_chat(
        user_message: str,
        mdb: MongoDBDatabase
) -> str:
    title = await create_chat_name(message=user_message)
    chat_obj = Chat(title=title)
    return await mdb.add_entry(chat_obj)

