import logging
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from app.llms.models import ChatLLM
from app.llms.utils import _get_messages_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIChat(ChatLLM):

    async def generate(
            self,
            message: str,
            system_message: Optional[str] = "You are a helpful AI assistant.",
            history: List[Dict[str, str]] = None
    ) -> str:
        client_params = {"api_key": self.chat_api.api_key}
        if self.chat_api.base_url is not None:
            client_params["base_url"] = self.chat_api.base_url

        client = AsyncOpenAI(**client_params)

        messages = _get_messages_template(message, system_message, history)

        try:
            response = await client.chat.completions.create(
                model=self.chat_model_config.model_name,
                messages=messages,
                max_tokens=500
            )
            logger.info("Successfully received response from OpenAI API")
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API request failed: {str(e)}")
            raise Exception(f"API Error: {str(e)}")