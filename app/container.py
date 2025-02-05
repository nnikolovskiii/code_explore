from dependency_injector import containers, providers
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

from app.chat.service import ChatService
from app.databases.mongo_db import MongoDBDatabase
from app.llms.llm_factory import LLMFactory
from app.telegram.telegram_bot import TelegramBot


def create_fernet():
    """Factory function to create Fernet instance with environment validation"""
    load_dotenv()
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        raise ValueError("ENCRYPTION_KEY environment variable is not set.")
    return Fernet(encryption_key.encode())  # Ensure proper encoding


class Container(containers.DeclarativeContainer):
    mdb = providers.Singleton(MongoDBDatabase)
    llm_factory = providers.Singleton(LLMFactory)

    fernet = providers.Singleton(create_fernet)

    telegram_bot = providers.Singleton(
        TelegramBot
    )

    chat_service = providers.Factory(
        ChatService,
        llm_factory=llm_factory,
        mdb=mdb,
        fernet=fernet
    )


container = Container()
