from typing import List, Dict, Optional

from openai import AsyncOpenAI

from app.llms.utils import _get_messages_template
from app.models.chat import ChatModel, ChatApi


async def openai_stream(
        message: str,
        system_message: str,
        chat_model: ChatModel,
        chat_api: ChatApi,
        history: List[Dict[str, str]] = None,
):
    client_params = {"api_key": chat_api.api_key}
    if chat_api.base_url is not None:
        client_params["base_url"] = chat_api.base_url

    client = AsyncOpenAI(**client_params)

    messages = _get_messages_template(message, system_message, history)

    stream = await client.chat.completions.create(
        model=chat_model.name,
        messages=messages,
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content