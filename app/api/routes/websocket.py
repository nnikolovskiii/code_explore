from datetime import datetime
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
from app.llms.chat.hf_inference_chat import InferenceClientChat
from app.llms.stream_chat.generic_stream_chat import generic_stream_chat
from app.models.Flag import Flag
import json

from app.pipelines.chat_title_pipeline import ChatTitlePipeline

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
                chat_id = await _create_chat(user_message=message, mdb=mdb)

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

            response = ""

            if docs_flag.active:
                async for response_chunk in chat(
                        message=message,
                        system_message="You are an expert coding assistant.",
                        history=history,
                        mdb=mdb
                ):
                    response += response_chunk
                    await websocket.send_text(response_chunk)
                    await asyncio.sleep(0.0001)
            else:
                async for response_chunk in generic_stream_chat(
                        message=message,
                        system_message="You are an expert coding assistant.",
                        history=history,
                        mdb=mdb
                ):
                    response += response_chunk
                    await websocket.send_text(response_chunk)
                    await asyncio.sleep(0.0001)

            await websocket.send_text("<ASTOR>")
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


async def _create_chat(
        mdb: MongoDBDatabase,
        user_message: str,
) -> str:
    chat_llm = await InferenceClientChat.create(model_name="Qwen/Qwen2.5-Coder-32B-Instruct")
    chat_name_pipeline = ChatTitlePipeline(chat_llm=chat_llm)
    response = await chat_name_pipeline.execute(message=user_message)

    chat_obj = Chat(title=response["title"])
    chat_obj.timestamp = datetime.now()

    return await mdb.add_entry(chat_obj)
