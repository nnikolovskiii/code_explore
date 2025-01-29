from typing import List, Dict, Optional, AsyncGenerator, Any

from openai import AsyncOpenAI

from app.llms.models import StreamChatLLM
from app.llms.utils import _get_messages_template

class OpenAIStreamChat(StreamChatLLM):

    async def generate(self, message: str, system_message: Optional[str] = "You are helpful AI assistant.",
                       history: List[Dict[str, str]] = None):
        client_params = {"api_key": self.chat_api.api_key}
        if self.chat_api.base_url is not None:
            client_params["base_url"] = self.chat_api.base_url

        client = AsyncOpenAI(**client_params)

        messages = _get_messages_template(message, system_message, history)

        stream = await client.chat.completions.create(
            model=self.chat_model_config.name,
            messages=messages,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

