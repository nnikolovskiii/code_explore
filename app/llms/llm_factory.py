from typing import TypeVar, Type

from pydantic import BaseModel

from app.llms.chat.inference_client_chat import InferenceClientChat
from app.llms.chat.ollama_chat import OllamaChat
from app.llms.chat.openai_chat import OpenAIChat
from app.llms.embedders.openai_embedder import OpenAIEmbeddingModel
from app.llms.models import ChatLLM, StreamChatLLM, EmbeddingModel, Reranker, BaseLLM
from app.llms.rerankers.cohere_reranker import CohereReranker
from app.llms.rerankers.nim_reranker import NimReranker
from app.llms.stream_chat.inference_client_stream import InferenceClientStreamChat
from app.llms.stream_chat.openai_stream import OpenAIStreamChat
from app.chat.models import ModelApi, ModelConfig

T = TypeVar('T', bound=BaseLLM)


class LLMFactory(BaseModel):
    @staticmethod
    def _create_chat_llm(
            chat_api: ModelApi,
            chat_model_config: ModelConfig,
    ) -> ChatLLM:
        if chat_api.type == "hugging_face":
            return InferenceClientChat(chat_api=chat_api, chat_model_config=chat_model_config)
        elif chat_api.type == "ollama":
            return OllamaChat(chat_api=chat_api, chat_model_config=chat_model_config)
        else:
            return OpenAIChat(chat_api=chat_api, chat_model_config=chat_model_config)

    @staticmethod
    def _create_stream_llm(
            chat_api: ModelApi,
            chat_model_config: ModelConfig,
    ) -> StreamChatLLM:
        if chat_api.type == "hugging_face":
            return InferenceClientStreamChat(chat_api=chat_api, chat_model_config=chat_model_config)
        else:
            return OpenAIStreamChat(chat_api=chat_api, chat_model_config=chat_model_config)

    @staticmethod
    def _create_embedding_model(
            chat_api: ModelApi,
            chat_model_config: ModelConfig,
    ) -> EmbeddingModel:
        if chat_api.type == "openai":
            return OpenAIEmbeddingModel(chat_api=chat_api, chat_model_config=chat_model_config)


    @staticmethod
    def _create_reranker_model(
            chat_api: ModelApi,
            chat_model_config: ModelConfig,
    ):
        if chat_api.type == "cohere":
            return CohereReranker(chat_api=chat_api, chat_model_config=chat_model_config)
        elif chat_api.type == "nim":
            return NimReranker(chat_api=chat_api, chat_model_config=chat_model_config)

    @staticmethod
    def create_model(
            chat_api: ModelApi,
            chat_model_config: ModelConfig,
            class_type: Type[T]
    ) -> BaseLLM:
        if issubclass(class_type, StreamChatLLM):
            return LLMFactory._create_stream_llm(chat_api, chat_model_config)
        elif issubclass(class_type, ChatLLM):
            return LLMFactory._create_chat_llm(chat_api, chat_model_config)
        elif issubclass(class_type, EmbeddingModel):
            return LLMFactory._create_embedding_model(chat_api, chat_model_config)
        elif issubclass(class_type, Reranker):
            return LLMFactory._create_reranker_model(chat_api, chat_model_config)
        else:
            raise Exception(f"There is no such class_type: {class_type}")

