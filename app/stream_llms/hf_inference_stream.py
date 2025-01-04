from typing import List, Dict

from huggingface_hub import InferenceClient

from app.llms.utils import _get_messages_template
from app.models.chat import ChatModel, ChatApi


async def chat_with_hf_inference_stream(
        message: str,
        system_message: str,
        chat_model: ChatModel,
        chat_api: ChatApi,
        history: List[Dict[str, str]] = None,
):
    client = InferenceClient(model=chat_model.name, api_key=chat_api.api_key, headers={"x-use-cache": "false"})

    messages = _get_messages_template(message, system_message, history)

    args = {"max_tokens": 15000, "messages": messages, "temperature": 0.5, "top_p": 0.8, "stream": True}

    for stream_output in client.chat_completion(**args):
        yield stream_output["choices"][0]["delta"]["content"]
