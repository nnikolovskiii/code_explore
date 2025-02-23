import datetime
from typing import Annotated
import asyncio

from bson import ObjectId
from fastapi import WebSocket
from pydantic_ai.messages import ModelRequest, SystemPromptPart, UserPromptPart, ModelResponse, TextPart

from app.api.routes.auth import get_current_user_websocket
from app.auth.models.user import User
from app.chat.chat import chat
import logging

from app.chat.models import Message, Chat
from app.container import container
from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.llms.models import StreamChatLLM
from app.models.flag import Flag
import json

logging.basicConfig(level=logging.DEBUG)
from fastapi import APIRouter, Depends

router = APIRouter()
mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]


@router.websocket("/")
async def websocket_endpoint(
        websocket: WebSocket,
        mdb: mdb_dep,
        current_user: User = Depends(get_current_user_websocket)
):
    chat_service = container.chat_service()

    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            data = json.loads(data)
            message, chat_id = data

            history = await chat_service.get_history_from_chat(chat_id=chat_id)
            message_history = convert_history(history)
            # print(message_history)
            if chat_id is None:
                chat_id = await chat_service.save_user_chat(user_message=message, user_email=current_user.email)

            chat_obj = await mdb.get_entry(ObjectId(chat_id), Chat)

            await mdb.add_entry(Message(
                role="user",
                content=message,
                order=chat_obj.num_messages,
                chat_id=chat_id
            ))

            docs_flag = await mdb.get_entry_from_col_values(
                columns={"name": "docs"},
                class_type=Flag
            )

            active_model = await chat_service.get_active_model(class_type=StreamChatLLM)
            # print(active_model.chat_model_config)
            # print(active_model.chat_api)

            response = ""

            if docs_flag.active:
                async for response_chunk in chat(
                        message=message,
                        system_message="You are an expert coding assistant.",
                        history=history,
                        active_model=active_model,
                        mdb=mdb
                ):
                    response += response_chunk
                    await websocket.send_text(response_chunk)
                    await asyncio.sleep(0.0001)
            else:
                async for response_chunk in active_model.generate(
                        message=message,
                        system_message="You are an expert coding assistant.",
                        history=history,
                ):
                    response += response_chunk
                    await websocket.send_text(response_chunk)
                    await asyncio.sleep(0.0001)

            await websocket.send_text(f"<ASTOR>:{chat_id}")
            await asyncio.sleep(0.1)

            await mdb.add_entry(Message(
                role="assistant",
                content=response,
                order=chat_obj.num_messages,
                chat_id=chat_id
            ))

            chat_obj.num_messages += 1
            await mdb.update_entry(chat_obj)

        except Exception as e:
            print(f"Error: {e}")
            break


def convert_history(history):
    if history is None or len(history) == 0:
        return None

    li = []
    message_request = get_system_messages()
    message_request.parts.append(
        UserPromptPart(content=history[0]["content"], timestamp=datetime.datetime.now(datetime.UTC),
                       part_kind='user-prompt'))
    li.append(message_request)

    for message in history[1:]:
        if message["role"] == "user":
            li.append(ModelRequest(
                parts=[UserPromptPart(
                    content=message["content"],
                    timestamp=datetime.datetime.now(datetime.UTC), part_kind='user-prompt')],
                kind='request'))

        elif message["role"] == "assistant":
            li.append(ModelResponse(
                parts=[
                    TextPart(
                        content=message["content"],
                        part_kind='text',
                    )
                ],
                timestamp=datetime.datetime.now(datetime.UTC),
                kind='response',
            ), )

    return li
