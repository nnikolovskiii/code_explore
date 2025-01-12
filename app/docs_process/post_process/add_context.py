import logging
from typing import List

from bson import ObjectId

from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from app.llms.generic_chat import generic_chat
from app.models.docs import DocsContent, DocsChunk, DocsContext, Link
from app.models.process import create_process, increment_process, finish_process, Process


class AddContextChunk(MongoEntry):
    chunk_id: str
    link: str
    url: str


def add_context_template(
        context: str,
        chunk_text: str
):
    return f"""<document> 
{context}
</document> 
Here is the chunk we want to situate within the whole document which is part of a code documentation.
<chunk> 
{chunk_text} 
</chunk> 
Give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Make it a couple of sentences long.
"""


async def _get_surrounding_context(
        chunk: DocsChunk,
        content: DocsContent,
        context_len: int
) -> str:
    start_index = chunk.start_index
    end_index = chunk.end_index
    content = content.content

    tmp1 = min(end_index + context_len, len(content))
    tmp2 = max(start_index - context_len, 0)

    if tmp2 == 0:
        tmp1 = min(end_index + context_len + (context_len - start_index), len(content))

    if tmp1 == len(content):
        tmp2 = max(start_index - context_len - (context_len - (len(content) - end_index)), 0)

    after_context = content[end_index:tmp1] + "..."
    before_context = "..." + content[tmp2:start_index]

    return before_context + chunk.content + after_context


async def add_context(
        chunk: DocsChunk,
        context_len: int,
        mdb: MongoDBDatabase
):
    if chunk.doc_len > 1:
        content = await mdb.get_entry(ObjectId(chunk.content_id), DocsContent)

        context = await _get_surrounding_context(chunk, content, context_len)
        template = add_context_template(context=context, chunk_text=chunk.content)
        response = await generic_chat(template,
                                      system_message="You are an AI assistant designed in providing contextual summaries and categorize documents.")
        await mdb.add_entry(DocsContext(
            base_url=chunk.base_url,
            link=chunk.link,
            chunk_id=chunk.id,
            context=response,
        ))


async def add_context_links(
        mdb: MongoDBDatabase,
        docs_url: str,
):
    process = await _get_add_context_length(mdb, docs_url)

    context_len = 50000
    count = 0

    async for chunk in mdb.stream_entries(
            class_type=AddContextChunk,
            doc_filter={"url": docs_url}
    ):
        await increment_process(process, mdb, count, 5)
        chunk = await mdb.get_entry(ObjectId(chunk.chunk_id), DocsChunk)

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


async def _get_add_context_length(
        mdb: MongoDBDatabase,
        docs_url: str,
) -> Process:
    await mdb.delete_entries(
        class_type=AddContextChunk,
        doc_filter={"url": docs_url, "processed": False,}
    )

    count = 0
    async for link_obj in mdb.stream_entries(
            class_type=Link,
            doc_filter={"base_url": docs_url, "processed": False},
            collection_name="TempLink"
    ):
        chunks = await mdb.get_entries(DocsChunk, doc_filter={"link": link_obj.link})
        chunks = [chunk for chunk in chunks if chunk.doc_len != 1]
        for chunk in chunks:
            if not chunk.context_processed:
                await mdb.add_entry(AddContextChunk(chunk_id=chunk.id, url=docs_url, link=chunk.link))
                count += 1

    process = await create_process(
        url=docs_url,
        end=count,
        process_type="context",
        mdb=mdb,
        type="docs"
    )

    return process
