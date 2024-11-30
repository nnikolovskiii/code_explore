from typing import List

from torch.utils.hipify.hipify_python import value

from app.databases.singletons import get_qdrant_db
from app.models.preprocess import FinalDocumentChunk


async def _get_chunk_tags(
        chunk: List[str]
)->str:
    chunk_tags = ""
    for i, chunk in enumerate(chunk):
        chunk_tags += f"""<chunk>\n{chunk}\n</chunk>"""
        if i < len(chunk)-1:
            chunk_tags += "\n"
    return chunk_tags

async def chat_template(
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
):
    qdb = await get_qdrant_db()

    points = await qdb.retrieve_similar_points(
        value=question,
        class_type=FinalDocumentChunk,
        score_threshold=0.2,
        top_k=15,
    )

