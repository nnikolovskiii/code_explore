import aiohttp
import logging
from typing import List, Dict, Optional
from app.llms.models import ChatLLM
from app.llms.utils import _get_messages_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InferenceClientChat(ChatLLM):

    async def generate(
            self,
            message: str,
            system_message: Optional[str] = "You are helpful AI assistant.",
            history: List[Dict[str, str]] = None
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.chat_api.api_key}",
            "Content-Type": "application/json"
        }

        messages = _get_messages_template(message, system_message, history)

        payload = {
            "max_tokens": 500,
            "messages": messages,
        }

        url = f"https://api-inference.huggingface.co/models/{self.chat_model_config.name}/v1/chat/completions"

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, json=payload) as response:
                logger.info(f"Received chat model response with status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    raise Exception(f"Error {response.status}: {response.reason}")
