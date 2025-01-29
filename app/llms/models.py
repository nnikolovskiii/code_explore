from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncGenerator, Any, Tuple
from app.chat.models import ChatApi, ChatModelConfig


class BaseLLM(ABC):
    chat_model_config: ChatModelConfig
    chat_api: ChatApi

    def __init__(self, chat_model_config: ChatModelConfig, chat_api: ChatApi):
        self.chat_model_config = chat_model_config
        self.chat_api = chat_api

    @abstractmethod
    async def generate(self, **kwargs):
        pass


class ChatLLM(BaseLLM):
    @abstractmethod
    async def generate(
            self,
            message: str,
            system_message: Optional[str] = "You are helpful AI assistant.",
            history: List[Dict[str, str]] = None
    ) -> str:
        pass


class StreamChatLLM(BaseLLM):
    @abstractmethod
    async def generate(
            self,
            message: str,
            system_message: Optional[str] = "You are helpful AI assistant.",
            history: List[Dict[str, str]] = None
    ):
        raise NotImplementedError()


class EmbeddingModel(BaseLLM):
    @abstractmethod
    async def generate(self, model_input: str) -> List[float]:
        pass


class Reranker(BaseLLM):
    @abstractmethod
    async def generate(
            self,
            query: str,
            documents: List[str],
            threshold: float,
            top_k: int
    ) -> List[Tuple[str, float]]:
        pass
