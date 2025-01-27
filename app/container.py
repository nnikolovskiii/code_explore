from dependency_injector import containers, providers

from app.chat.service import ChatService
from app.databases.mongo_db import MongoDBDatabase


class Container(containers.DeclarativeContainer):
    mdb = providers.Singleton(MongoDBDatabase)

    chat_service = providers.Factory(
        ChatService,
        mdb=mdb
    )

container = Container()
