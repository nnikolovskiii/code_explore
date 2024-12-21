import logging
from typing import List

from bson import ObjectId

from app.databases.mongo_db import MongoDBDatabase
from app.llms.generic_chat import generic_chat
from app.llms.json_response import get_json_response
from app.models.docs import DocsContent, DocsChunk, DocsEmbeddingFlag, DocsContext
from app.models.process import create_process, increment_process, finish_process


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
        links: List[str],
        docs_url: str,
):
    process = await create_process(
        url=docs_url,
        end=await _get_add_context_length(mdb, docs_url, links),
        process_type="context",
        mdb=mdb,
        type="docs"
    )

    context_len = 50000
    count = 0

    async for chunk in mdb.stream_entries_dict(
            collection_name="ProcessChunk",
            doc_filter={"url": docs_url, "process": "context"}
    ):
        chunk_id = chunk["chunk_id"]
        chunk = await mdb.get_entry(ObjectId(chunk_id), DocsChunk)

        await increment_process(process, mdb, count, 5)

        while True:
            try:
                await add_context(chunk, context_len, mdb)
                break
            except Exception as e:
                logging.info(f"Adjusting the context_length. Current context length: {context_len}")
                context_len-=500
                logging.error(e)

            if context_len < 1000:
                context_len = 50000
                break

        count += 1
        logging.info(count)


    await finish_process(process, mdb)
    await mdb.delete_entries(
        class_type=DocsChunk,
        collection_name="ProcessChunk",
        doc_filter={"url": docs_url, "process": "context"})


async def _get_add_context_length(
        mdb: MongoDBDatabase,
        docs_url: str,
        links: List[str],
) -> int:
    await mdb.delete_entries(
        class_type=DocsChunk,
        collection_name="ProcessChunk",
        doc_filter={"url": docs_url, "process": "context"})

    count = 0
    for link in links:
        flag = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=DocsEmbeddingFlag
        )

        if flag is None:
            chunks = await mdb.get_entries(DocsChunk, doc_filter={"link": link})
            chunks = [chunk for chunk in chunks if chunk.doc_len != 1]
            for chunk in chunks:
                if count == 100:
                    return count
                context = await mdb.get_entry_from_col_value(
                    column_name="chunk_id",
                    column_value=chunk.id,
                    class_type=DocsContext
                )
                if context is None:
                    await mdb.add_entry_dict({"chunk_id": chunk.id, "process": "context", "url": docs_url},
                                             "ProcessChunk")
                    count += 1
    return count
