from typing import Optional

from app.container import container
from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from app.llms.models import EmbeddingModel

mdb = None

async def get_mongo_db(url: Optional[str] = None) -> MongoDBDatabase:
    global mdb
    if mdb is None:
        mdb = MongoDBDatabase(url=url)
    return mdb

qdb = None

async def get_qdrant_db() -> QdrantDatabase:
    global qdb
    if qdb is None:
        qdb = QdrantDatabase()
        chat_service = container.chat_service()
        embedding_model = await chat_service.get_model("text-embedding-3-large", EmbeddingModel)
        await qdb.set_embedding_model(embedding_model)
    return qdb