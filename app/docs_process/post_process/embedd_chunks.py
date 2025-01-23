import asyncio
import logging

from bson import ObjectId

from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from app.databases.qdrant_db import QdrantDatabase

from app.models.docs import DocsChunk, DocsContext, Link
from app.models.process import create_process, increment_process, finish_process, Process

logger = logging.getLogger(__name__)


class EmbeddChunk(MongoEntry):
    chunk_id: str
    url: str
    link: str


async def embedd_chunks(
        mdb: MongoDBDatabase,
        docs_url: str,
        qdb: QdrantDatabase,
):
    process = await _create_embedd_process(docs_url, mdb)

    if process is None:
        return

    count = 0
    async for chunk in mdb.stream_entries(
            class_type=EmbeddChunk,
            doc_filter={"url": docs_url}
    ):
        await increment_process(process, mdb, count, 5)

        chunk = await mdb.get_entry(ObjectId(chunk.chunk_id), DocsChunk)

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
                metadata={"active": True}
            )

            chunk.processed = True
            await mdb.update_entry(chunk)

        except Exception as e:
            logging.error(e)

        count += 1

    await finish_process(process, mdb)
    await mdb.delete_entries(
        class_type=EmbeddChunk,
        doc_filter={"url": docs_url})

    await _set_embedding_flags(docs_url, mdb)


async def _set_embedding_flags(
        docs_url: str,
        mdb: MongoDBDatabase
):
    async for link_obj in mdb.stream_entries(
            class_type=Link,
            doc_filter={"base_url": docs_url, "processed": False, "active": True},
    ):
        num_processed_chunks = await mdb.count_entries(DocsChunk, doc_filter={"link": link_obj.link, "base_url": docs_url,
                                                                              "processed": True})
        first_chunk = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link_obj.link,
            class_type=DocsChunk
        )

        if first_chunk and first_chunk.doc_len == num_processed_chunks:
            link_obj.processed = True
            await mdb.update_entry(link_obj)
        elif num_processed_chunks == 0:
            link_obj.processed = True
            await mdb.update_entry(link_obj)


async def _create_embedd_process(
        docs_url: str,
        mdb: MongoDBDatabase
) -> Process | None:
    await mdb.delete_entries(
        class_type=EmbeddChunk,
        doc_filter={"url": docs_url})

    count = 0
    async for link_obj in mdb.stream_entries(
            class_type=Link,
            doc_filter={"base_url": docs_url, "processed": False, "active": True},
    ):
        chunks = await mdb.get_entries(DocsChunk, doc_filter={"link": link_obj.link})
        for chunk in chunks:
            if not chunk.processed:
                await mdb.add_entry(EmbeddChunk(chunk_id=chunk.id, url=docs_url, link=chunk.link))
                count += 1

    if count > 0:
        return await create_process(
            url=docs_url,
            end=count,
            curr=0,
            process_type="embedd",
            mdb=mdb,
            type="docs",
            group="post"
        )

    return None


# asyncio.run(_set_embedding_flags("https://docs.expo.dev", mdb= MongoDBDatabase()))