import logging
from typing import List

from bson import ObjectId

from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase

from app.models.docs import DocsChunk, DocsContext, DocsEmbeddingFlag, Link
from app.models.process import create_process, increment_process, finish_process

logger = logging.getLogger(__name__)


async def embedd_chunks(
        mdb: MongoDBDatabase,
        links: List[str],
        docs_url: str,
        qdb: QdrantDatabase,
):
    logging.info("get length")
    process = await create_process(
        url=docs_url,
        end=await _get_embedd_chunks_length(links, docs_url, mdb),
        process_type="embedd",
        mdb=mdb,
        type="docs"
    )

    count = 0
    async for chunk in mdb.stream_entries_dict(
            collection_name="ProcessChunk",
            doc_filter={"url": docs_url, "process": "embedd"}
    ):
        chunk_id = chunk["chunk_id"]
        chunk = await mdb.get_entry(ObjectId(chunk_id), DocsChunk)
        await increment_process(process, mdb, count, 5)

        context = await mdb.get_entry_from_col_value(
            column_name="chunk_id",
            column_value=chunk.id,
            class_type=DocsContext
        )
        if context is not None:
            chunk.content = context.context + chunk.content

        try:
            await qdb.embedd_and_upsert_record(
                value=chunk.content,
                entity=chunk,
                metadata={"active": False}
            )
        except Exception as e:
            logging.error(e)

        chunk.processed = True
        await mdb.update_entry(chunk)
        count += 1

    await finish_process(process, mdb)
    await mdb.delete_entries(
        class_type=DocsChunk,
        collection_name="ProcessChunk",
        doc_filter={"url": docs_url, "process": "embedd"})

    await _set_embedding_flags(links, docs_url, mdb)

async def _set_embedding_flags(
        links: List[str],
        docs_url: str,
        mdb: MongoDBDatabase
):
    for link in links:
        link_obj = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=Link
        )

        if link_obj and not link_obj.processed:
            num_processed_chunks = await mdb.count_entries(DocsChunk, doc_filter={"link": link,"base_url":docs_url, "processed": True})
            first_chunk = await mdb.get_entry_from_col_value(
                column_name="link",
                column_value=link,
                class_type=DocsChunk
            )

            if first_chunk and first_chunk.doc_len == num_processed_chunks:
                link_obj.processed = True
                await mdb.update_entry(link_obj)


async def _get_embedd_chunks_length(
        links: List[str],
        docs_url: str,
        mdb: MongoDBDatabase
) -> int:
    await mdb.delete_entries(
        class_type=DocsChunk,
        collection_name="ProcessChunk",
        doc_filter={"url": docs_url, "process": "embedd"})

    count = 0
    for link in links:
        chunks = await mdb.get_entries(DocsChunk, doc_filter={"link": link})
        for chunk in chunks:
            if not chunk.processed:
                await mdb.add_entry_dict({"chunk_id": chunk.id, "process": "embedd", "url": docs_url},
                                         "ProcessChunk")
                count += 1
    return count
