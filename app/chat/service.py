from datetime import datetime, timedelta
from typing import Tuple, TypeVar, Type

from cryptography.fernet import Fernet
from groq.types import Embedding

from app.llms.llm_factory import LLMFactory
from app.llms.models import BaseLLM, StreamChatLLM, Reranker, ChatLLM, EmbeddingModel
from app.chat.models import Message, Chat, ModelApi, ModelConfig
from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from app.models.flag import Flag
from app.pipelines.chat_title_pipeline import ChatTitlePipeline


class ActiveModelDto(MongoEntry):
    model: str
    type: str


T = TypeVar('T', bound=BaseLLM)


class ChatService:
    mdb: MongoDBDatabase
    llm_factory: LLMFactory
    fernet: Fernet

    def __init__(self, mdb: MongoDBDatabase, llm_factory: LLMFactory, fernet: Fernet) -> None:
        self.mdb = mdb
        self.llm_factory = llm_factory
        self.fernet = fernet

    async def get_chats_by_datetime(self):
        chats = await self.mdb.get_entries(Chat)
        chats = sorted(chats, key=lambda x: x.timestamp, reverse=True)

        categorized_chats = {
            "today": [],
            "yesterday": [],
            "previous_7_days": [],
            "previous_30_days": []
        }
        now = datetime.now()

        for chat in chats:
            category = self._categorize_chat_by_datetime(chat, now)
            if category:
                categorized_chats[category].append(chat)

        for category in categorized_chats:
            categorized_chats[category].sort(key=lambda x: x.timestamp, reverse=True)

        return categorized_chats

    @staticmethod
    def _categorize_chat_by_datetime(chat, now):
        chat_datetime = chat.timestamp

        if chat_datetime.date() == now.date():
            return "today"
        elif chat_datetime.date() == (now - timedelta(days=1)).date():
            return "yesterday"
        elif now - timedelta(days=7) <= chat_datetime <= now:
            return "previous_7_days"
        elif now - timedelta(days=30) <= chat_datetime <= now:
            return "previous_30_days"
        return None

    async def add_model_api(self, model_api: ModelApi):
        encrypted_bytes = self.fernet.encrypt(model_api.api_key.encode('utf-8'))
        model_api.api_key = encrypted_bytes.decode('utf-8')

        model_api_obj = await self.mdb.get_entry_from_col_value(
            column_name="type",
            column_value=model_api.type,
            class_type=ModelApi
        )

        if model_api_obj is None:
            await self.mdb.add_entry(model_api)
        else:
            model_api_obj.api_key = model_api.api_key
            model_api_obj.base_url = model_api.base_url
            await self.mdb.update_entry(model_api_obj)

    async def add_model_config(self, model_config: ModelConfig):
        model_config_obj = await self.mdb.get_entry_from_col_value(
            column_name="name",
            column_value=model_config.name,
            class_type=ModelConfig
        )

        model_api = await self.mdb.get_entry_from_col_value(
            column_name="type",
            column_value=model_config.chat_api_type,
            class_type=ModelApi
        )
        if model_api is None:
            raise Exception("Model API does not exist")

        if model_config_obj is None:
            await self.mdb.add_entry(model_config)
        else:
            model_config_obj.name = model_config.name
            model_config_obj.chat_api_type = model_config.chat_api_type
            await self.mdb.update_entry(model_config_obj)

    async def get_api_models(self, type: str, model_type: str):
        chat_api = await self.mdb.get_entry_from_col_value(
            column_name="type",
            column_value=type,
            class_type=ModelApi
        )

        if chat_api is None:
            raise Exception("Chat API does not exist")

        # chat_api.api_key = self.fernet.decrypt(chat_api.api_key).decode()
        return {
            "models": await self.mdb.get_entries(ModelConfig,
                                                 doc_filter={"chat_api_type": type, "model_type": model_type}),
            "api": None
        }

    async def set_active_model(self, active_model_dto: ActiveModelDto, model_type: str):
        current_active = await self.mdb.get_entry_from_col_values(
            columns={"active": True, "model_type": model_type},
            class_type=ModelConfig
        )

        if current_active is not None:
            current_active.active = False
            await self.mdb.update_entry(current_active)

        new_active = await self.mdb.get_entry_from_col_values(
            columns={"name": active_model_dto.model, "model_type": model_type},
            class_type=ModelConfig
        )

        if new_active is None:
            raise Exception("Chat Model does not exist")
        else:
            new_active.active = True
            await self.mdb.update_entry(new_active)

    async def get_messages_from_chat(
            self,
            chat_id: str,
    ):
        user_messages = await self.mdb.get_entries(Message, doc_filter={"chat_id": chat_id, "role": "user"})
        assistant_messages = await self.mdb.get_entries(Message, doc_filter={"chat_id": chat_id, "role": "assistant"})

        user_messages = sorted(user_messages, key=lambda x: x.order)
        assistant_messages = sorted(assistant_messages, key=lambda x: x.order)

        return {"user_messages": user_messages, "assistant_messages": assistant_messages}

    async def get_history_from_chat(
            self,
            chat_id: str,
    ):
        history = []
        history_flag = await self.mdb.get_entry_from_col_value(
            column_name="name",
            column_value="history",
            class_type=Flag
        )

        if history_flag.active and chat_id is not None:
            messages = await self.get_messages_from_chat(chat_id=chat_id)
            user_messages = messages["user_messages"]
            assistant_messages = messages["assistant_messages"]

            for i in range(len(user_messages)):
                history.append({"role": "user", "content": user_messages[i].content})
                if i < len(assistant_messages):
                    history.append({"role": "user", "content": assistant_messages[i].content})

        return history

    async def save_user_chat(
            self,
            user_message: str,
    ) -> str:
        chat_llm = await self.get_model(model_name="deepseek-chat", class_type=ChatLLM)
        chat_name_pipeline = ChatTitlePipeline(chat_llm=chat_llm)
        response = await chat_name_pipeline.execute(message=user_message)

        chat_obj = Chat(title=response["title"])
        chat_obj.timestamp = datetime.now()

        return await self.mdb.add_entry(chat_obj)

    async def get_active_model_config(self, model_type: str) -> Tuple[ModelConfig, ModelApi]:
        model_config = await self.mdb.get_entry_from_col_values(
            columns={"active": True, "model_type": model_type},
            class_type=ModelConfig,
        )

        model_api = await self.get_model_api(type=model_config.chat_api_type)

        return model_config, model_api

    async def get_model_api(self, type: str) -> ModelApi:
        model_api = await self.mdb.get_entry_from_col_value(
            column_name="type",
            column_value=type,
            class_type=ModelApi,
        )
        encrypted_bytes = model_api.api_key.encode('utf-8')
        model_api.api_key = self.fernet.decrypt(encrypted_bytes).decode()
        return model_api

    async def get_model_config(self, model_name) -> Tuple[ModelConfig, ModelApi]:
        model_config = await self.mdb.get_entry_from_col_values(
            columns={"name": model_name},
            class_type=ModelConfig,
        )

        chat_api = await self.get_model_api(model_config.chat_api_type)

        if model_config is None or chat_api is None:
            raise Exception(f"Model {model_name} not found")

        return model_config, chat_api

    async def get_model(self, model_name: str, class_type: Type[T]) -> T:
        model_config, chat_api = await self.get_model_config(model_name)
        return self.llm_factory.create_model(chat_api=chat_api, chat_model_config=model_config, class_type=class_type)

    async def get_active_model(self, class_type: Type[T]) -> T:
        model_type = self._get_model_type_from_class(class_type)
        model_config, chat_api = await self.get_active_model_config(model_type=model_type)
        return self.llm_factory.create_model(chat_api=chat_api, chat_model_config=model_config, class_type=class_type)

    @staticmethod
    def _get_model_type_from_class(class_type: Type[T]) -> str:
        if issubclass(class_type, StreamChatLLM):
            return "chat"
        elif issubclass(class_type, ChatLLM):
            return "chat"
        elif issubclass(class_type, EmbeddingModel):
            return "embedding"
        elif issubclass(class_type, Reranker):
            return "reranker"
        else:
            raise Exception(f"Unknown type {class_type}")
