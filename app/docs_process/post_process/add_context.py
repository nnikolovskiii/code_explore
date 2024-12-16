from typing import List

from bson import ObjectId
from tqdm import tqdm

from app.databases.mongo_db import MongoDBDatabase
from app.llms.json_response import get_json_response
from app.models.docs import DocsContent, DocsChunk, DocsEmbeddingFlag, DocsContext


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


async def add_context_chunks(
        mdb: MongoDBDatabase,
        chunks: List[DocsChunk],
):
    filtered_chunks = [chunk for chunk in chunks if chunk.doc_len != 1]
    for chunk in tqdm(filtered_chunks):
        try:
            await add_context(chunk, 8000, mdb)
        except Exception as e:
            print(e)

async def add_context_links(
        mdb: MongoDBDatabase,
        links: List[str],
        docs_url: str,
):
    embedded_flags = await mdb.get_entries(DocsEmbeddingFlag, doc_filter={"base_url": docs_url})
    embedded_links = {flag.link for flag in embedded_flags}

    chunks = []
    for link in links:
        if link not in embedded_links:
            link_chunks = await mdb.get_entries(DocsChunk, doc_filter={"link": link})
            chunks.extend(link_chunks)
    await add_context_chunks(mdb, chunks)
