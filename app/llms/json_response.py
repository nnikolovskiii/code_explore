import os
from typing import Any, Dict
import logging
from pydantic import BaseModel

from dotenv import load_dotenv

from app.databases.mongo_db import MongoDBDatabase
from app.llms.generic_chat import generic_chat
from app.utils.json_extraction import trim_and_load_json


class ChatResponse(BaseModel):
    message: str
    response: str
    llm_model: str


async def get_json_response(
        template: str,
        store_in_db: bool = True,
        list_name: str = "",
        system_message: str = "You are a helpful AI assistant."
) -> Dict[str, Any]:
    mdb = MongoDBDatabase()
    chat_model = os.getenv("CHAT_MODEL")

    is_finished = False
    json_data = {}
    tries = 0
    response = ""
    while not is_finished:
        if tries > 0:
            logging.warning(f"Chat not returning as expected. it: {tries}")

        if tries > 3:
            if tries > 0:
                logging.warning("Chat not returning as expected.")
            raise Exception()

        response = await generic_chat(message=template, system_message=system_message)

        if store_in_db:
            await mdb.add_entry(entity=ChatResponse(message=template, response=response, llm_model=chat_model),
                          metadata={"version": 1})

        is_finished, json_data = await trim_and_load_json(input_string=response, list_name=list_name)
        tries += 1

    load_dotenv()

    return json_data
