from datetime import datetime
from typing import Tuple

from cryptography.fernet import Fernet

from app.llms.llm_factory import LLMFactory
from app.llms.models import ChatLLM, StreamChatLLM, EmbeddingModel
from app.chat.models import Message, Chat, ChatApi, ChatModelConfig
from app.databases.mongo_db import MongoDBDatabase
from app.models.Flag import Flag
from app.pipelines.chat_title_pipeline import ChatTitlePipeline


class ChatService:
    mdb: MongoDBDatabase
    llm_factory: LLMFactory
    fernet: Fernet

    def __init__(self, mdb: MongoDBDatabase, llm_factory: LLMFactory, fernet: Fernet) -> None:
        self.mdb = mdb
        self.llm_factory = llm_factory
        self.fernet = fernet

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
        chat_llm = await self.get_chat_llm(model_name="Qwen/Qwen2.5-Coder-32B-Instruct")
        chat_name_pipeline = ChatTitlePipeline(chat_llm=chat_llm)
        response = await chat_name_pipeline.execute(message=user_message)

        chat_obj = Chat(title=response["title"])
        chat_obj.timestamp = datetime.now()

        return await self.mdb.add_entry(chat_obj)

    async def get_active_chat_model(self) -> Tuple[ChatModelConfig, ChatApi]:
        chat_model = await self.mdb.get_entry_from_col_value(
            column_name="active",
            column_value=True,
            class_type=ChatModelConfig,
        )

        chat_api = await self.get_chat_api(type=chat_model.chat_api_type)

        return chat_model, chat_api

    async def get_chat_api(self, type: str) -> ChatApi:
        chat_api = await self.mdb.get_entry_from_col_value(
            column_name="type",
            column_value=type,
            class_type=ChatApi,
        )
        encrypted_bytes = chat_api.api_key.encode('utf-8')
        chat_api.api_key = self.fernet.decrypt(encrypted_bytes).decode()
        return chat_api

    async def get_model_config(self, model_name)->Tuple[ChatModelConfig, ChatApi]:
        chat_model_config = await self.mdb.get_entry_from_col_values(
            columns={"name": model_name},
            class_type=ChatModelConfig,
        )

        chat_api = await self.get_chat_api(chat_model_config.chat_api_type)

        if chat_model_config is None or chat_api is None:
            raise Exception(f"Model {model_name} not found")

        return chat_model_config, chat_api

    async def get_chat_llm(self, model_name) -> ChatLLM:
        chat_model_config, chat_api = await self.get_model_config(model_name)
        return self.llm_factory.crete_chat_llm(chat_api=chat_api, chat_model_config=chat_model_config)

    async def get_embedding_model(self, model_name) -> EmbeddingModel:
        chat_model_config, chat_api = await self.get_model_config(model_name)
        return self.llm_factory.create_embedding_model(chat_api=chat_api, chat_model_config=chat_model_config)


    async def get_active_stream_chat(self)->StreamChatLLM:
        chat_model_config ,chat_api = await self.get_active_chat_model()
        return self.llm_factory.create_stream_llm(chat_api=chat_api, chat_model_config=chat_model_config)
