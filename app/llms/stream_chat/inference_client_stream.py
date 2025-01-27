from typing import List, Dict
import asyncio

from huggingface_hub import InferenceClient

from app.llms.utils import _get_messages_template
from app.models.chat import ChatModel, ChatApi


async def chat_with_inference_stream(
        message: str,
        system_message: str,
        chat_model: ChatModel,
        chat_api: ChatApi,
        history: List[Dict[str, str]] = None,
):
    client = InferenceClient(model=chat_model.name, api_key=chat_api.api_key, headers={"x-use-cache": "false"})
    messages = _get_messages_template(message, system_message, history)
    args = {"max_tokens": 15000, "messages": messages, "temperature": 0.5, "top_p": 0.8, "stream": True}

    loop = asyncio.get_event_loop()
    sync_gen = client.chat_completion(**args)

    while True:
        try:
            stream_output = await loop.run_in_executor(
                None,
                lambda g: next(g, None),
                sync_gen
            )

            if stream_output is None:
                break

            if stream_output.get("choices"):
                content = stream_output["choices"][0]["delta"].get("content", "")
                yield content

        except Exception as e:
            print(f"Streaming error: {str(e)}")
            break