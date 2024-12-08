from typing import List

from app.code_process.post_process.add_context import add_context_chunks
from app.code_process.post_process.embedd_chunks import create_final_chunks, embedd_chunks
from app.code_process.pre_process.extract_content import chunk_files
from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase


async def process_code_files(
        file_paths: List[str],
        git_url: str,
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase,
):
    chunks = await chunk_files(file_paths=file_paths, git_url=git_url, mdb=mdb)
    contexts = await add_context_chunks(mdb=mdb, chunks=chunks)
    final_chunks = await create_final_chunks(mdb=mdb, chunks=chunks, contexts=contexts)
    await embedd_chunks(mdb=mdb, qdb=qdb, chunks=final_chunks)