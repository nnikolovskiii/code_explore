import aiohttp
import logging
from typing import List, Dict, Optional
from app.llms.models import ChatLLM
from app.llms.utils import _get_messages_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaChat(ChatLLM):

    async def generate(
            self,
            message: str,
            system_message: Optional[str] = "You are a helpful AI assistant.",
            history: List[Dict[str, str]] = None
    ) -> str:
        url = 'http://localhost:11434/api/chat'

        messages = _get_messages_template(message, system_message, history)

        payload = {
            'model': self.chat_model_config.model_name,
            'messages': messages,
            'stream': False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                logger.info(f"Received Ollama response with status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    return data['message']['content']
                else:
                    response_text = await response.text()
                    logger.error(f"Ollama API request failed: {response_text}")
                    raise Exception(f"Error {response.status}: {response.reason}")