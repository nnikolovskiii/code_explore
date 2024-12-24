import asyncio
from typing import List, Dict

from app.databases.singletons import get_qdrant_db, get_mongo_db
from app.models.code import CodeChunk, GitUrl
from app.models.docs import DocsChunk, DocsUrl
from app.stream_llms.hf_inference_stream import chat_with_hf_inference_stream


def _get_chunk_tags(
        chunk: List[str]
) -> str:
    chunk_tags = ""
    for i, chunk in enumerate(chunk):
        chunk_tags += f"""<chunk>\n{chunk}\n</chunk>"""
        if i < len(chunk) - 1:
            chunk_tags += "\n"
    return chunk_tags


def chat_template(
        chunks: List[str],
        question
):
    return f"""Below you are given a question and relevant chunks which are retrieved from a vector database.
Here are the chunks which are most similar to the question.
{_get_chunk_tags(chunks)}
Here is the question from the user:
<question>
{question}
</question>

Your job is to provide a correct and detailed answer to the question.
Important: Use your own knowledge to determine which information from the chunks is relevant when answering the question.
"""


async def retrieve_relevant_chunks(
        question: str
) -> List[DocsChunk]:
    qdb = await get_qdrant_db()
    mdb = await get_mongo_db()

    docs_objs = await mdb.get_entries(DocsUrl, doc_filter={"active": True})
    docs_urls = [docs_obj.url for docs_obj in docs_objs]

    return await qdb.retrieve_similar_entries(
        value=question,
        class_type=DocsChunk,
        score_threshold=0.0,
        top_k=10,
        filter={("active", "value"): True, ("base_url", "any") : docs_urls}
    )


async def chat(
        message: str,
        system_message: str,
        history: List[Dict[str, str]] = None,
        stream: bool = False,
):
    relevant_chunks = await retrieve_relevant_chunks(message)
    chunk_contents = [chunk.content for chunk in relevant_chunks]
    template = chat_template(chunk_contents, message)
    async for data in chat_with_hf_inference_stream(
        message=template,
        system_message=system_message,
        history=history,
        stream=stream,
    ):
        yield data
