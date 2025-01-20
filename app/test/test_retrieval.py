import asyncio
from typing import List

from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from app.models.docs import DocsChunk
from app.test.create_question_flow import Question
from tqdm import tqdm


async def test_retrieval(top_k: int) -> None:
    mdb= MongoDBDatabase()
    qdb = QdrantDatabase()

    questions = await mdb.get_entries(Question)
    counter1 = 0
    counter2 = 0
    for question_obj in tqdm(questions):

        no_context_retrieved= await qdb.retrieve_similar_entries(
            value=question_obj.question,
            class_type=DocsChunk,
            score_threshold=0.0,
            top_k=top_k,
            filter={("base_url", "any") : ["https://docs.expo.dev"]},
            collection_name="Test"
        )
        context_retrieved = await qdb.retrieve_similar_entries(
            value=question_obj.question,
            class_type=DocsChunk,
            score_threshold=0.0,
            top_k=top_k,
            filter={("base_url", "any") : ["https://docs.expo.dev"]},
            collection_name="DocsChunk"
        )

        no_context_ids = {chunk.id for chunk in no_context_retrieved}
        context_ids = {chunk.id for chunk in context_retrieved}

        if question_obj.chunk_id in no_context_ids:
            counter1 += 1
        if question_obj.chunk_id in context_ids:
            counter2 += 1

    print(counter1, counter2)

asyncio.run(test_retrieval(10))