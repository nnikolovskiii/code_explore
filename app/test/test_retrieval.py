import asyncio
from typing import List

from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from app.models.docs import DocsChunk
from app.test.create_question_flow import Question


async def retrieve_relevant_chunks(
        question: str,
        qdb: QdrantDatabase,
        top_k: int
) -> List[DocsChunk]:
    return await qdb.retrieve_similar_entries(
        value=question,
        class_type=DocsChunk,
        score_threshold=0.0,
        top_k=top_k,
        filter={("base_url", "any") : ["https://docs.expo.dev"]}
    )


async def test_retrieval(top_k: int) -> None:
    mdb_local = MongoDBDatabase(url="localhost")
    mdb_server = MongoDBDatabase(url="mkpatka.duckdns.org")
    qdb_local = QdrantDatabase(url="localhost")
    qdb_server = QdrantDatabase(url="mkpatka.duckdns.org")

    questions = await mdb_local.get_entries(Question)
    counter1 = 0
    counter2 = 0
    for question_obj in questions:
        no_context_retrieved= await retrieve_relevant_chunks(question_obj.question, qdb_local, top_k)
        context_retrieved = await retrieve_relevant_chunks(question_obj.question, qdb_server, top_k)

        no_context_links = {chunk.link for chunk in no_context_retrieved}
        context_links = {chunk.link for chunk in context_retrieved}

        if question_obj.link in no_context_links:
            counter1 += 1
        if question_obj.link in context_links:
            counter2 += 1

    print(counter1, counter2)

asyncio.run(test_retrieval(5))