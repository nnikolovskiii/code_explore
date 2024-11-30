from http import HTTPStatus
from typing import Annotated

from fastapi import HTTPException, APIRouter, Depends

from app.chat.models import Message, Chat
import logging

from app.databases.singletons import get_mongo_db

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

db_dep = Annotated[dict, Depends(get_mongo_db)]

@router.post("/add_message/", status_code=HTTPStatus.CREATED)
async def add_message(message:Message, mdb: db_dep):
    try:
        message = await mdb.add_entry(message)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
    return message

@router.get("/add_chat/", status_code=HTTPStatus.CREATED)
async def add_chat(mdb: db_dep):
    try:
        chat = Chat()
        chat = await mdb.add_entry(chat)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
    return chat


@router.get("/add_chat/", status_code=HTTPStatus.CREATED)
async def add_chat(mdb: db_dep):
    try:
        chat = Chat()
        chat = mdb.add_entry(chat)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
    return chat

@router.get("/get_messages/", status_code=HTTPStatus.CREATED)
async def get_messages_from_chat(chat_id: str, mdb: db_dep):
    try:
        messages = await mdb.get_entries(Message, doc_filter={"chat_id": chat_id})
        messages = sorted(messages, key=lambda m: m.timestamp)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to get messages")
    return messages
