import logging
from typing import List

from bson import ObjectId

from app.databases.mongo_db import MongoDBDatabase
from app.llms.json_response import get_json_response
from app.models.docs import DocsContent, DocsChunk, DocsEmbeddingFlag, DocsContext
from app.models.process import  create_process, increment_process, finish_process


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
Give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
Return in json format: {{"context": "..."}}
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
    content = await mdb.get_entry(ObjectId(chunk.content_id), DocsContent)

    context = await _get_surrounding_context(chunk, content, context_len)
    template = add_context_template(context=context, chunk_text=chunk.content)
    response = await get_json_response(template,
                                       system_message="You are an AI assistant designed in providing contextual summaries and categorize documents.")
    await mdb.add_entry(DocsContext(
        base_url=chunk.base_url,
        link=chunk.link,
        chunk_id=chunk.id,
        context=response["context"],
    ))

async def add_context_links(
        mdb: MongoDBDatabase,
        links: List[str],
        docs_url: str,
):
    process = await create_process(
        url=docs_url,
        end= await _get_add_context_length(mdb, links),
        process_type = "context",
        mdb = mdb,
        type = "docs"
    )

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
                await increment_process(process, mdb, count,5)

                context = await mdb.get_entry_from_col_value(
                    column_name="chunk_id",
                    column_value=chunk.id,
                    class_type=DocsContext
                )
                if context is None:
                    try:
                        await add_context(chunk, 8000, mdb)
                    except Exception as e:
                        logging.error(e)
                    count += 1

    await finish_process(process, mdb)


async def _get_add_context_length(
        mdb: MongoDBDatabase,
        links: List[str],
) -> int:
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
                context = await mdb.get_entry_from_col_value(
                    column_name="chunk_id",
                    column_value=chunk.id,
                    class_type=DocsContext
                )
                if context is None:
                    count += 1

    return count