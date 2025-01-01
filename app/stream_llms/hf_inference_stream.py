import os
from typing import List, Dict

from huggingface_hub import InferenceClient
from dotenv import load_dotenv

from app.llms.utils import _get_messages_template


async def chat_with_hf_inference_stream(
        message: str,
        system_message: str,
        history: List[Dict[str, str]] = None,
):
    load_dotenv()
    hf_api_key = os.getenv("HF_API_KEY")
    hf_model = os.getenv("HF_MODEL")

    client = InferenceClient(model=hf_model, api_key=hf_api_key, headers={"x-use-cache": "false"})

    messages = _get_messages_template(message, system_message, history)

    args = {"max_tokens": 15000, "messages": messages, "temperature": 0.5, "top_p": 0.8, "stream": True}

    for stream_output in client.chat_completion(**args):
        yield stream_output["choices"][0]["delta"]["content"]
