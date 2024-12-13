from http import HTTPStatus
from typing import Annotated

from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel

from app.chat.create_chat_name import create_chat_name
from app.chat.models import Message, Chat
import logging

from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

db_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]

class ChatDto(BaseModel):
    user_messages: list[str]
    assistant_messages: list[str]

@router.get("/get_chats/", status_code=HTTPStatus.CREATED)
async def get_chats(mdb: db_dep):
    try:
        chats = await mdb.get_entries(Chat)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
    return chats


@router.post("/add_chat/", status_code=HTTPStatus.CREATED)
async def add_chat(chat_dto: ChatDto, mdb: db_dep):
    try:
        user_messages = chat_dto.user_messages

        if len(user_messages) == 0:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="There are no user messages")
        title = await create_chat_name(message=user_messages[0])
        chat_obj = Chat(title=title)
        chat_obj_id = await mdb.add_entry(chat_obj)
        for i,message in enumerate(user_messages):
            await mdb.add_entry(Message(
                role="user",
                content=message,
                order= i,
                chat_id=chat_obj_id
            ))

        for i,message in enumerate(chat_dto.assistant_messages):
            await mdb.add_entry(Message(
                role="assistant",
                content=message,
                order= i,
                chat_id=chat_obj_id
            ))

    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
    return True
