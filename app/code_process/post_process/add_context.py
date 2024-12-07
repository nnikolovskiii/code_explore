import asyncio
from typing import List

from bson import ObjectId
from tqdm import tqdm

from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.llms.generic_chat import generic_chat
from app.llms.json_response import get_json_response
from app.models.code import CodeChunk, CodeContent, CodeContext
from app.models.docs import Content, DocumentChunk, Context, Category, FinalDocumentChunk


def add_context_template(
        context: str,
        chunk_text: str
):
    return f"""<code> 
{context}
</code> 
Here is the code chunk we want to situate within the whole code file.
<code_chunk> 
{chunk_text} 
</code_chunk> 
Give a short succinct context to situate this code chunk within the overall code file for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. 
"""

async def _get_surrounding_context(
        chunk:DocumentChunk,
        content: Content,
        context_len:int
) -> str:
    start_index = chunk.start_index
    end_index = chunk.end_index
    content = content.content

    tmp1 = min(end_index + context_len, len(content))
    tmp2 = max(start_index - context_len, 0)

    if tmp2 == 0:
        tmp1 = min(end_index + context_len + (context_len-start_index), len(content))

    if tmp1 == len(content):
        tmp2 = max(start_index - context_len - (context_len - (len(content) - end_index)), 0)

    after_context = content[end_index:tmp1] + "..."
    before_context = "..." + content[tmp2:start_index]

    return before_context + chunk.content + after_context


async def add_context(
    chunk: CodeChunk,
    context_len: int
):
    mdb = await get_mongo_db()
    content = await mdb.get_entry(ObjectId(chunk.content_id),CodeContent)

    context = await _get_surrounding_context(chunk, content, context_len)
    template = add_context_template(context=context, chunk_text=chunk.content)
    response = await generic_chat(template, system_message="You are an AI assistant designed in providing contextual summaries of code.")
    await mdb.add_entry(CodeContext(
        url=chunk.url,
        chunk_id=chunk.id,
        context=response,
    ),metadata={"order": chunk.order})


async def add_context_all(
        mdb: MongoDBDatabase,
        git_url: str,
):
    chunks = await mdb.get_entries(CodeChunk, doc_filter={"url": git_url})
    filtered_chunks = [chunk for chunk in chunks if chunk.code_len != 1]

    for chunk in tqdm(filtered_chunks):
        try:
            await add_context(chunk, 8000)
        except Exception as e:
            print(e)


async def add_context_files(
        mdb: MongoDBDatabase,
        file_paths: List[str],
):
    chunks = []
    for file_path in file_paths:
        content = await mdb.get_entry_from_col_value(
            column_name="file_path",
            column_value=file_path,
            class_type=CodeContent
        )

        li = await mdb.get_entries(CodeChunk, doc_filter={"content_id": content.id})
        chunks.extend(li)

    filtered_chunks = [chunk for chunk in chunks if chunk.code_len != 1]

    for chunk in tqdm(filtered_chunks):
        try:
            await add_context(chunk, 8000)
        except Exception as e:
            print(e)

