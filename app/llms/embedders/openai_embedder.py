import asyncio
import os
from dotenv import load_dotenv
import httpx
from typing import List

from openai import AsyncOpenAI

from app.llms.models import EmbeddingModel


class OpenAIEmbeddingModel(EmbeddingModel):
    async def generate(self, model_input: str) -> List[float]:
        client = AsyncOpenAI(api_key=self.chat_api.api_key)

        try:
            response = await client.embeddings.create(
                input=model_input,
                model=self.chat_model_config.name
            )
            return response.data[0].embedding
        except Exception as e:
            raise e
