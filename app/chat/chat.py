import asyncio
from typing import List, Dict

from torch.utils.hipify.hipify_python import value

from app.databases.singletons import get_qdrant_db, get_mongo_db
from app.llms.generic_chat import generic_chat
from app.models.code import CodeChunk, GitUrl
from app.models.docs import FinalDocumentChunk
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

Your job is to provide a correct and detailed answer to the question. Break your answer into multiple step in order for the user to easily understand it.
"""


async def retrieve_relevant_chunks(
        question: str
) -> List[CodeChunk]:
    qdb = await get_qdrant_db()
    mdb = await get_mongo_db()

    git_objs = await mdb.get_entries(GitUrl, doc_filter={"active": True})
    git_urls = [git_obj.url for git_obj in git_objs]

    return await qdb.retrieve_similar_entries(
        value=question,
        class_type=CodeChunk,
        score_threshold=0.0,
        top_k=5,
        filter={("active", "value"): True, ("url", "any"): git_urls}
    )


async def chat(
        message: str,
        system_message: str,
        history: List[Dict[str, str]] = None,
        stream: bool = False,
):
    relevant_chunks = await retrieve_relevant_chunks(message)
    print(relevant_chunks)
    print(len(relevant_chunks))
    chunk_contents = [chunk.content for chunk in relevant_chunks]
    template = chat_template(chunk_contents, message)
    async for data in chat_with_hf_inference_stream(
        message=template,
        system_message=system_message,
        history=history,
        stream=stream,
    ):
        yield data
