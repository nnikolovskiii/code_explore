import asyncio
import logging
from typing import List, final

from bson import ObjectId

from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.code import CodeChunk, CodeContent, CodeContext, CodeEmbeddingFlag
from tqdm import tqdm

logger = logging.getLogger(__name__)


async def create_final_chunks(
        mdb: MongoDBDatabase,
        chunks: List[CodeChunk],
        contexts: List[CodeContext]
)->List[CodeChunk]:

    contexts_dict = {context.chunk_id: context.context for context in contexts}

    final_chunks = []

    count_context = 0
    count_all = 0
    for chunk in tqdm(chunks, total=len(chunks)):
        content = chunk.content

        if chunk.id in contexts_dict:
            content = contexts_dict[chunk.id] + content
            count_context += 1

        chunk.content = content

        await mdb.update_entry(chunk)
        final_chunks.append(chunk)
        count_all += 1

    if len(chunks)>0:
        logger.info(f"{count_context / len(chunks) * 100:.2f}% of chunks had context added")
        logger.info(f"{count_all / len(chunks) * 100:.2f}% of chunks were successfully added to the database")

    return final_chunks


async def embedd_chunks(
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase,
        chunks: List[CodeChunk]
):
    file_paths_set = {chunk.file_path for chunk in chunks}

    for chunk in tqdm(chunks):
        await qdb.embedd_and_upsert_record(
            value=chunk.content,
            entity=chunk
        )

    if len(chunks) > 0:
        for file_path in file_paths_set:
            await mdb.add_entry(CodeEmbeddingFlag(
                url=chunks[0].url,
                file_path=file_path,
            ))
