import asyncio
from typing import List, Dict

from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.models.chat import get_active_chat_model, get_chat_api
from app.stream_llms.inference_client_stream import chat_with_inference_stream
from app.stream_llms.openai_stream import openai_stream


async def generic_stram_chat(
        message: str,
        mdb: MongoDBDatabase = None,
        history: List[Dict[str, str]] = None,
        system_message: str = "You are a helpful AI assistant.",
):
    chat_model = await get_active_chat_model(mdb)
    print(chat_model)
    chat_api = await get_chat_api(type=chat_model.chat_api_type, mdb=mdb)

    if chat_model.chat_api_type == "openai":
        async for data in openai_stream(message, system_message, chat_model,chat_api, history):
            yield data
    elif chat_model.chat_api_type == "hugging_face":
        async for data in chat_with_inference_stream(message, system_message, chat_model,chat_api, history):
            yield data
    elif chat_model.chat_api_type == "deepseek":
        async for data in openai_stream(message, system_message, chat_model,chat_api, history):
            yield data

async def _test_generic_stram_chat():
    mdb = await get_mongo_db()
    async for response_chunk in generic_stram_chat(
            message="Hello what are you primarily designed to do. Answer in one sentence?" ,
            system_message="You are an expert coding assistant.",
            mdb=mdb,
    ):
        print(response_chunk)

# asyncio.run(_test_generic_stram_chat())