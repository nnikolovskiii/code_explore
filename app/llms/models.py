from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from app.chat.service import ChatService
from app.container import container
from app.models.chat import ChatModel, ChatApi


class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, **kwargs):
        pass

class ChatLLM(BaseLLM):
    chat_service: ChatService = container.chat_service()
    chat_model: ChatModel
    chat_api: ChatApi

    def __init__(self, chat_model: ChatModel, chat_api: ChatApi):
        self.chat_model = chat_model
        self.chat_api = chat_api

    @classmethod
    async def create(cls, model_name: str):
        chat_service = container.chat_service()
        chat_api, chat_model = await chat_service.get_model_and_api(model_name)
        return cls(chat_model, chat_api)

    @abstractmethod
    async def generate(
            self,
            message: str,
            system_message: Optional[str] = "You are helpful AI assistant.",
            history: List[Dict[str, str]] = None
    ) -> str:
        pass

class EmbeddingModel(BaseLLM):
    def generate(self, **kwargs):
        pass

class Reranker(BaseLLM):  # Simplified name
    def generate(self, **kwargs):
        pass