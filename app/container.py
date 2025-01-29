from dependency_injector import containers, providers

from app.chat.service import ChatService
from app.databases.mongo_db import MongoDBDatabase
from app.llms.llm_factory import LLMFactory


class Container(containers.DeclarativeContainer):
    mdb = providers.Singleton(MongoDBDatabase)
    llm_factory = providers.Singleton(LLMFactory)

    chat_service = providers.Factory(
        ChatService,
        llm_factory=llm_factory,
        mdb=mdb
    )

container = Container()
