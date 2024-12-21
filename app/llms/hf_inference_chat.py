import aiohttp
import asyncio
import os
from typing import List, Dict
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from app.llms.utils import _get_messages_template

async def chat_with_hf_inference(
    message: str,
    system_message: str,
    history: List[Dict[str, str]] = None,
    stream: bool = False
):
    load_dotenv()
    hf_api_key = os.getenv("HF_API_KEY")
    hf_model = os.getenv("HF_MODEL")

    headers = {
        "Authorization": f"Bearer {hf_api_key}",
        "Content-Type": "application/json"
    }

    messages = _get_messages_template(message, system_message, history)

    payload = {
        "max_tokens": 500,
        "messages": messages,
        "stream": stream
    }

    url = f"https://api-inference.huggingface.co/models/{hf_model}/v1/chat/completions"

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                print(data['choices'][0]['message']['content'])
                return data['choices'][0]['message']['content']
            else:
                raise Exception(f"Error {response.status}: {response.reason}")
