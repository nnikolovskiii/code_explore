from typing import List, Dict

from openai import OpenAI

from app.llms.utils import _get_messages_template
from app.models.chat import ChatModel, ChatApi


async def openai_stream(
        message: str,
        system_message: str,
        chat_model: ChatModel,
        chat_api: ChatApi,
        history: List[Dict[str, str]] = None,
):
    client = OpenAI(api_key=chat_api.api_key)
    messages = _get_messages_template(message, system_message, history)

    stream = client.chat.completions.create(
        model=chat_model.name,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content

