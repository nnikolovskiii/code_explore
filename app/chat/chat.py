from typing import List, Dict

from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_qdrant_db
from app.stream_llms.generic_stream_chat import generic_stram_chat
from app.models.docs import DocsChunk, DocsUrl


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
        question: str,
        mdb: MongoDBDatabase,
) -> List[DocsChunk]:
    qdb = await get_qdrant_db()
    docs_objs = await mdb.get_entries(DocsUrl, doc_filter={"active": True})
    docs_urls = [docs_obj.url for docs_obj in docs_objs]
    return await qdb.retrieve_similar_entries(
        value=question,
        class_type=DocsChunk,
        score_threshold=0.3,
        top_k=10,
        filter={("active", "value"): True, ("base_url", "any") : docs_urls}
    )


async def chat(
        message: str,
        system_message: str,
        mdb: MongoDBDatabase,
        history: List[Dict[str, str]] = None,
):
    relevant_chunks = await retrieve_relevant_chunks(message, mdb=mdb)
    references = {(relevant_chunk.link, relevant_chunk.link.split(relevant_chunk.base_url)[1]) for relevant_chunk in relevant_chunks}
    chunk_contents = [chunk.content for chunk in relevant_chunks]
    template = chat_template(chunk_contents, message)
    async for data in generic_stram_chat(
            message=template,
            system_message=system_message,
            history=history,
            mdb=mdb
    ):
        yield data

    yield "<div class='references'><p class='reference_header'>Sources:</p><div class='references_list'>"
    for reference, reference_name in references:
        yield f"""<div class="reference">
                        <a href="{reference}" target="_blank">
                            {reference_name}
                        </a>
                      </div>"""
    yield "</div></div>"
