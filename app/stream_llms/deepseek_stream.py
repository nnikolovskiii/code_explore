import asyncio
import os
from typing import List, Dict

from dotenv import load_dotenv
from openai import OpenAI
from app.llms.utils import _get_messages_template


async def deepseek_stream(
        message: str,
        system_message: str,
        history: List[Dict[str, str]] = None,
):
    load_dotenv()
    openai_api_key = os.getenv("DEEPSEEK_API_KEY")
    openai_model = os.getenv("DEEPSEEK_MODEL")

    client = OpenAI(api_key=openai_api_key, base_url="https://api.deepseek.com")
    messages = _get_messages_template(message, system_message, history)

    stream = client.chat.completions.create(
        model=openai_model,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content

async def _test_deepseek_stream():
    async for chunk in deepseek_stream("Hello what are you primarily designed to do. Answer in one sentence?", "You are a helpful financial AI assistant."):
        print(chunk)
asyncio.run(_test_deepseek_stream())
