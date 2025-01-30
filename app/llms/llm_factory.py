from pydantic import BaseModel

from app.llms.chat.inference_client_chat import InferenceClientChat
from app.llms.chat.ollama_chat import OllamaChat
from app.llms.chat.openai_chat import OpenAIChat
from app.llms.embedders.openai_embedder import OpenAIEmbeddingModel
from app.llms.models import ChatLLM, StreamChatLLM, EmbeddingModel
from app.llms.stream_chat.inference_client_stream import InferenceClientStreamChat
from app.llms.stream_chat.openai_stream import OpenAIStreamChat
from app.chat.models import ModelApi, ModelConfig


class LLMFactory(BaseModel):
    @staticmethod
    def crete_chat_llm(
            chat_api:ModelApi,
            chat_model_config:ModelConfig,
    )->ChatLLM:
        if chat_api.type == "hugging_face":
            return InferenceClientChat(chat_api=chat_api, chat_model_config=chat_model_config)
        elif chat_api.type == "ollama":
            return OllamaChat(chat_api=chat_api, chat_model_config=chat_model_config)
        else:
            return OpenAIChat(chat_api=chat_api, chat_model_config=chat_model_config)

    @staticmethod
    def create_stream_llm(
            chat_api:ModelApi,
            chat_model_config:ModelConfig,
    )->StreamChatLLM:
        if chat_api.type == "hugging_face":
            return InferenceClientStreamChat(chat_api=chat_api, chat_model_config=chat_model_config)
        else:
            return OpenAIStreamChat(chat_api=chat_api, chat_model_config=chat_model_config)

    @staticmethod
    def create_embedding_model(
            chat_api:ModelApi,
            chat_model_config:ModelConfig,
    )->EmbeddingModel:
        if chat_api.type == "openai":
            return OpenAIEmbeddingModel(chat_api=chat_api, chat_model_config=chat_model_config)
