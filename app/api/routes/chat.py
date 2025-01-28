from http import HTTPStatus
from typing import Tuple, List

from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

from app.chat.models import Chat
import logging

from app.container import container
from app.databases.mongo_db import MongoEntry
from app.models.chat import ChatApi, get_fernet, ChatModel
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()


class ChatDto(BaseModel):
    user_messages: list[str]
    assistant_messages: list[str]


class MessagesDto(BaseModel):
    user_messages: List[Tuple[str, int]]
    assistant_messages: List[Tuple[str, int]]


@router.get("/get_chats/", status_code=HTTPStatus.CREATED)
async def get_chats():
    mdb = container.mdb()

    def categorize_chat(chat, now):
        chat_datetime = chat.timestamp

        if chat_datetime.date() == now.date():
            return "today"
        elif chat_datetime.date() == (now - timedelta(days=1)).date():
            return "yesterday"
        elif now - timedelta(days=7) <= chat_datetime <= now:
            return "previous_7_days"
        elif now - timedelta(days=30) <= chat_datetime <= now:
            return "previous_30_days"
        return None

    try:
        chats = await mdb.get_entries(Chat)
        chats = sorted(chats, key=lambda x: x.timestamp, reverse=True)

        categorized_chats = {
            "today": [],
            "yesterday": [],
            "previous_7_days": [],
            "previous_30_days": []
        }
        now = datetime.now()

        for chat in chats:
            category = categorize_chat(chat, now)
            if category:
                categorized_chats[category].append(chat)

        # Sort the chats within each category from latest to oldest
        for category in categorized_chats:
            categorized_chats[category].sort(key=lambda x: x.timestamp, reverse=True)

    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")

    return categorized_chats


@router.get("/get_chat_messages/{chat_id}", status_code=HTTPStatus.CREATED)
async def get_chat_messages(chat_id: str):
    chat_service = container.chat_service()
    try:
        return await chat_service.get_messages_from_chat(chat_id=chat_id)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")


@router.post("/add_chat_api/", status_code=HTTPStatus.CREATED)
async def add_chat_api(chat_api: ChatApi):
    mdb = container.mdb()

    try:
        chat_api.api_key = get_fernet().encrypt(chat_api.api_key.encode())
        chat_api_obj = await mdb.get_entry_from_col_value(
            column_name="type",
            column_value=chat_api.type,
            class_type=ChatApi
        )

        if chat_api_obj is None:
            await mdb.add_entry(chat_api)
        else:
            chat_api_obj.api_key = chat_api.api_key
            chat_api_obj.base_url = chat_api.base_url
            await mdb.update_entry(chat_api_obj)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
    return True


@router.post("/add_chat_model/", status_code=HTTPStatus.CREATED)
async def add_chat_model(chat_model: ChatModel):
    mdb = container.mdb()

    try:
        chat_model_obj = await mdb.get_entry_from_col_value(
            column_name="name",
            column_value=chat_model.name,
            class_type=ChatModel
        )

        chat_api = await mdb.get_entry_from_col_value(
            column_name="type",
            column_value=chat_model.chat_api_type,
            class_type=ChatApi
        )
        if chat_api is None:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Chat API does not exist")

        if chat_model_obj is None:
            await mdb.add_entry(chat_model)
        else:
            chat_model_obj.name = chat_model.name
            chat_model_obj.chat_api_type = chat_model.chat_api_type
            await mdb.update_entry(chat_model_obj)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
    return True


@router.get("/get_chat_api_and_models/", status_code=HTTPStatus.CREATED)
async def get_chat_api_and_models(type: str):
    mdb = container.mdb()

    try:
        chat_api = await mdb.get_entry_from_col_value(
            column_name="type",
            column_value=type,
            class_type=ChatApi
        )

        if chat_api is None:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Chat API does not exist")

        chat_api.api_key = get_fernet().decrypt(chat_api.api_key).decode()
        return {
            "models": await mdb.get_entries(ChatModel, doc_filter={"chat_api_type": type}),
            "api": chat_api
        }
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")


class ActiveModelDto(MongoEntry):
    model: str
    type: str


@router.post("/set_active_model/", status_code=HTTPStatus.CREATED)
async def set_active_model(active_model_dto: ActiveModelDto):
    mdb = container.mdb()

    try:
        current_active = await mdb.get_entry_from_col_value(
            column_name="active",
            column_value=True,
            class_type=ChatModel
        )

        if current_active is not None:
            current_active.active = False
            await mdb.update_entry(current_active)

        new_active = await mdb.get_entry_from_col_value(
            column_name="name",
            column_value=active_model_dto.model,
            class_type=ChatModel
        )

        if new_active is None:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Chat Model does not exist")
        else:
            new_active.active = True
            await mdb.update_entry(new_active)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")


@router.get("/get_active_model/", status_code=HTTPStatus.CREATED)
async def get_active_model():
    mdb = container.mdb()
    chat_service = container.chat_service()

    try:
        chat_model = await chat_service.get_active_chat_model()
        return chat_model
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
