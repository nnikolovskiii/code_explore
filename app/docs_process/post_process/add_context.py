import logging

from bson import ObjectId

from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from app.api.pipelines.chunk_context_pipeline import ChunkContextPipeline
from app.models.docs import DocsChunk, Link, DocsContent, DocsContext
from app.models.process import create_process, increment_process, finish_process, Process


class AddContextChunk(MongoEntry):
    chunk_id: str
    link: str
    url: str


async def add_context(
        chunk: DocsChunk,
        context_len: int,
        mdb: MongoDBDatabase
):
    if chunk.doc_len > 1:
        context = await _get_surrounding_context(chunk=chunk, context_len=context_len, mdb=mdb)
        pipeline = ChunkContextPipeline()
        response = await pipeline.execute(context=context, chunk_text=chunk.content)
        await mdb.add_entry(DocsContext(
            base_url=chunk.base_url,
            link=chunk.link,
            chunk_id=chunk.id,
            context=response,
        ))

async def _get_surrounding_context(
        chunk: DocsChunk,
        mdb: MongoDBDatabase,
        context_len: int
) -> str:
    start_index = chunk.start_index
    end_index = chunk.end_index

    content_obj = await mdb.get_entry(ObjectId(chunk.content_id), DocsContent)
    content = content_obj.content

    tmp1 = min(end_index + context_len, len(content))
    tmp2 = max(start_index - context_len, 0)

    if tmp2 == 0:
        tmp1 = min(end_index + context_len + (context_len - start_index), len(content))

    if tmp1 == len(content):
        tmp2 = max(start_index - context_len - (context_len - (len(content) - end_index)), 0)

    after_context = content[end_index:tmp1] + "..."
    before_context = "..." + content[tmp2:start_index]

    return before_context + chunk.content + after_context

async def add_context_links(
        mdb: MongoDBDatabase,
        docs_url: str,
):
    process = await _create_context_process(mdb, docs_url)

    if process is None:
        return

    context_len = 50000
    count = 0

    async for add_context_chunk in mdb.stream_entries(
            class_type=AddContextChunk,
            doc_filter={"url": docs_url}
    ):
        await increment_process(process, mdb, count, 5)
        chunk = await mdb.get_entry(ObjectId(add_context_chunk.chunk_id), DocsChunk)

        while True:
            try:
                await add_context(chunk, context_len, mdb)
                chunk.context_processed = True
                await mdb.update_entry(chunk)
                break
            except Exception as e:
                logging.info(f"Adjusting the context_length. Current context length: {context_len}")
                context_len -= 500
                logging.error(e)

            if context_len < 1000:
                context_len = 50000
                break

        count += 1

    await finish_process(process, mdb)
    await mdb.delete_entries(
        class_type=AddContextChunk,
        doc_filter={"url": docs_url}
    )


async def _create_context_process(
        mdb: MongoDBDatabase,
        docs_url: str,
) -> Process | None:
    await mdb.delete_entries(
        class_type=AddContextChunk,
        doc_filter={"url": docs_url}
    )

    count = 0
    async for link_obj in mdb.stream_entries(
            class_type=Link,
            doc_filter={"base_url": docs_url, "processed": False, "active": True},
    ):
        chunks = await mdb.get_entries(DocsChunk, doc_filter={"link": link_obj.link})
        chunks = [chunk for chunk in chunks if chunk.doc_len != 1]
        for chunk in chunks:
            if not chunk.context_processed:
                await mdb.add_entry(AddContextChunk(chunk_id=chunk.id, url=docs_url, link=chunk.link))
                count += 1

    if count > 0:
        return await create_process(
            url=docs_url,
            curr=0,
            end=count,
            process_type="context",
            mdb=mdb,
            type="docs",
            group="post",
        )

    return None
