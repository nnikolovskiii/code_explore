from typing import Any, Dict
import logging
from dotenv import load_dotenv

from app.llms.generic_chat import generic_chat, ChatModel
from app.utils.json_extraction import trim_and_load_json


async def get_json_response(
        template: str,
        list_name: str = "",
        system_message: str = "You are a helpful AI assistant.",
        chat_model: str = None
) -> Dict[str, Any]:
    is_finished = False
    json_data = {}
    tries = 0

    while not is_finished:
        if tries > 0:
            logging.warning(f"Chat not returning as expected. it: {tries}")

        if tries > 3:
            if tries > 0:
                logging.warning("Chat not returning as expected.")
            raise Exception()

        response = await generic_chat(
            message=template,
            system_message=system_message,
            chat_model=chat_model,
        )

        is_finished, json_data = await trim_and_load_json(input_string=response, list_name=list_name)
        tries += 1

    load_dotenv()

    return json_data
