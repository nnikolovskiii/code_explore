from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncGenerator, Any
from app.models.chat import ChatModelConfig, ChatApi


class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, **kwargs):
        pass

class ChatLLM(BaseLLM):
    chat_model_config: ChatModelConfig
    chat_api: ChatApi

    def __init__(self, chat_model_config: ChatModelConfig, chat_api: ChatApi):
        self.chat_model_config = chat_model_config
        self.chat_api = chat_api

    @abstractmethod
    async def generate(
            self,
            message: str,
            system_message: Optional[str] = "You are helpful AI assistant.",
            history: List[Dict[str, str]] = None
    ) -> str:
        pass

class StreamChatLLM(BaseLLM):
    chat_model_config: ChatModelConfig
    chat_api: ChatApi

    def __init__(self, chat_model_config: ChatModelConfig, chat_api: ChatApi):
        self.chat_model_config = chat_model_config
        self.chat_api = chat_api

    async def generate(
            self,
            message: str,
            system_message: Optional[str] = "You are helpful AI assistant.",
            history: List[Dict[str, str]] = None
    ):
        raise NotImplementedError()

class EmbeddingModel(BaseLLM):
    def generate(self, **kwargs):
        pass

class Reranker(BaseLLM):  # Simplified name
    def generate(self, **kwargs):
        pass