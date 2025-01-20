from typing import Annotated
import asyncio
from fastapi import WebSocket

from app.chat.chat import chat
import logging

from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.llms.generic_stream_chat import generic_stram_chat
from app.models.Flag import Flag
import json

logging.basicConfig(level=logging.DEBUG)
from fastapi import APIRouter, Depends

router = APIRouter()
mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, mdb: mdb_dep):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            data = json.loads(data)
            message, user_messages, assistant_messages = data

            history = []
            history_flag = await mdb.get_entry_from_col_value(
                column_name="name",
                column_value="history",
                class_type=Flag
            )

            if history_flag.active:
                for i in range(len(user_messages)):
                    history.append({"role": "user", "content": user_messages[i]})
                    if i < len(assistant_messages):
                        history.append({"role": "user", "content": assistant_messages[i]})

            docs_flag = await mdb.get_entry_from_col_value(
                column_name="name",
                column_value="docs",
                class_type=Flag
            )

            if docs_flag.active:
                async for response_chunk in chat(
                    message=message,
                    system_message="You are an expert coding assistant.",
                    history=history,
                    mdb=mdb
                ):
                    await websocket.send_text(response_chunk)
                    await asyncio.sleep(0.0001)
            else:
                async for response_chunk in generic_stram_chat(
                        message=message,
                        system_message="You are an expert coding assistant.",
                        history=history,
                        mdb=mdb
                ):
                    await websocket.send_text(response_chunk)
                    await asyncio.sleep(0.0001)

            await websocket.send_text("<ASTOR>")
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error: {e}")
            break