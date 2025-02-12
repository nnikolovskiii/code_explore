from typing import Annotated
import asyncio

from bson import ObjectId
from fastapi import WebSocket

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
async def websocket_endpoint(websocket: WebSocket, mdb: mdb_dep):
    chat_service = container.chat_service()

    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            data = json.loads(data)
            message, chat_id = data

            history = await chat_service.get_history_from_chat(chat_id=chat_id)
            if chat_id is None:
                chat_id = await chat_service.save_user_chat(user_message=message)

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
            print(active_model.chat_model_config)
            print(active_model.chat_api)

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

