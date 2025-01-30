from http import HTTPStatus
from typing import Tuple, List

from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

from app.chat.models import ModelApi, ModelConfig
import logging

from app.chat.service import ActiveModelDto
from app.container import container


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
    chat_service = container.chat_service()

    try:
        categorized_chats = await chat_service.get_chats_by_datetime()
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
async def add_chat_api(model_api: ModelApi):
    chat_service = container.chat_service()

    try:
        await chat_service.add_model_api(model_api)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
    return True


@router.post("/add_chat_model/", status_code=HTTPStatus.CREATED)
async def add_chat_model(model_config: ModelConfig):
    chat_service = container.chat_service()

    try:
        await chat_service.add_model_config(model_config)
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
    return True


@router.get("/get_chat_api_and_models/", status_code=HTTPStatus.CREATED)
async def get_chat_api_and_models(type: str):
    chat_service = container.chat_service()

    try:
        return await chat_service.get_api_models(type=type, model_type="chat")
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")



@router.post("/set_active_model/", status_code=HTTPStatus.CREATED)
async def set_active_model(active_model_dto: ActiveModelDto):
    chat_service = container.chat_service()

    try:
        return await chat_service.set_active_model(active_model_dto=active_model_dto, model_type="chat")
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")


@router.get("/get_active_model/", status_code=HTTPStatus.CREATED)
async def get_active_model():
    chat_service = container.chat_service()

    try:
        chat_model, _ = await chat_service.get_active_model_config(model_type="chat")
        return chat_model
    except Exception as e:
        logging.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to add entry")
