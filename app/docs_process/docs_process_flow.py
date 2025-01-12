import logging
from typing import List

from pydantic import BaseModel

from app.code_process.post_process.active_status import update_records
from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from app.docs_process.post_process.add_context import add_context_links
from app.docs_process.post_process.embedd_chunks import embedd_chunks
from app.docs_process.post_process.chunking import chunk_links
from app.models.docs import Link, DocsChunk


class DocsActiveListDto(BaseModel):
    links: List[str]
    active: List[bool]


async def process_code_files(
        docs_url: str,
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase,
):
    logging.info("chunk_links")
    await chunk_links(docs_url=docs_url, mdb=mdb)
    logging.info("add_context_links")
    # await add_context_links(mdb=mdb, docs_url=docs_url)
    logging.info("embedd_chunks")
    await embedd_chunks(mdb=mdb, qdb=qdb, docs_url=docs_url)


async def change_active_files(
        docs_url: str,
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase
):
    await mdb.delete_entries(
        class_type=Link,
        doc_filter={"base_url": docs_url, "processed": False, "active": False},
        collection_name="TempLink"
    )

    await process_code_files(
        docs_url=docs_url,
        mdb=mdb,
        qdb=qdb,
    )

    async for link_obj in mdb.stream_entries(Link, doc_filter={"base_url": docs_url}, collection_name="TempLink"):
        await mdb.update_entry(link_obj, collection_name="Link")

        await update_records(
            qdb=qdb,
            collection_name="DocsChunk",
            filter={("link", "value"): link_obj.link},
            update={"active": link_obj.active},
        )

        chunks = await mdb.get_entries(
            DocsChunk,
            doc_filter={"link": link_obj.link}
        )
        for chunk in chunks:
            chunk.active = link_obj.active
            await mdb.update_entry(chunk)
