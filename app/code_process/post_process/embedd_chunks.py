import asyncio
import logging
from typing import List

from bson import ObjectId

from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.code import CodeChunk, CodeContent, CodeContext
from tqdm import tqdm

logger = logging.getLogger(__name__)


async def create_final_chunks(mdb: MongoDBDatabase, chunks: List[CodeChunk], contexts: List[CodeContext]):
    file_path_dict = {}
    for chunk in chunks:
        content = await mdb.get_entry(id=ObjectId(chunk.content_id), class_type=CodeContent)
        file_path_dict[chunk.id] = content.file_path

    contexts_dict = {context.chunk_id: context.context for context in contexts}

    count_context = 0
    count_all = 0
    for chunk in tqdm(chunks, total=len(chunks)):
        content = chunk.content

        if chunk.id in contexts_dict:
            content = contexts_dict[chunk.id] + content
            count_context += 1

        chunk.content = content

        await mdb.update_entry(chunk)
        count_all += 1

    logger.info(f"{count_context / len(chunks) * 100:.2f}% of chunks had context added")
    logger.info(f"{count_all / len(chunks) * 100:.2f}% of chunks were successfully added to the database")


async def create_final_chunks_all_code(
        mdb: MongoDBDatabase,
        git_url: str,
):
    chunks = await mdb.get_entries(CodeChunk, doc_filter={"url": git_url})
    contexts = await mdb.get_entries(CodeContext, doc_filter={"url": git_url})
    await create_final_chunks(mdb, chunks, contexts)


async def create_final_chunks_files(
        mdb: MongoDBDatabase,
        file_paths: List[str],
):
    chunks = []
    for file_path in file_paths:
        li = await mdb.get_entries(CodeChunk, doc_filter={"file_path": file_path})
        chunks.extend(li)

    contexts = []
    for file_path in file_paths:
        li = await mdb.get_entries(CodeContext, doc_filter={"file_path": file_path})
        contexts.extend(li)

    await create_final_chunks(mdb, chunks, contexts)


async def embedd_chunks(
        qdb: QdrantDatabase,
        chunks: List[CodeChunk]
):
    for chunk in tqdm(chunks):
        await qdb.embedd_and_upsert_record(
            value=chunk.content,
            entity=chunk
        )

async def embedd_chunks_all_code(
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase,
        git_url: str,
):
    chunks = await mdb.get_entries(CodeChunk, doc_filter={"url": git_url})
    await embedd_chunks(qdb, chunks[:10])


async def embedd_chunks_files(
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase,
        file_paths: List[str],
):
    chunks = []
    for file_path in file_paths:
        li = await mdb.get_entries(CodeChunk, doc_filter={"file_path": file_path})
        chunks.extend(li)

    await embedd_chunks(qdb, chunks)