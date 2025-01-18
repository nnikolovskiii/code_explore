import logging

from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from app.docs_process.post_process.add_context import add_context_links
from app.docs_process.post_process.embedd_chunks import embedd_chunks
from app.docs_process.post_process.chunking import chunk_links


async def process_links_flow(
        docs_url: str,
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase
):
    logging.info("chunk_links")
    await chunk_links(docs_url=docs_url, mdb=mdb)
    logging.info("add_context_links")
    await add_context_links(mdb=mdb, docs_url=docs_url)
    logging.info("embedd_chunks")
    await embedd_chunks(mdb=mdb, qdb=qdb, docs_url=docs_url)

