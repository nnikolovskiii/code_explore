import asyncio
import random
import re

from app.databases.mongo_db import MongoEntry, MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.docs_process.post_process.add_context import _get_surrounding_context
from app.models.docs import DocsChunk, Link, DocsContext
from app.test.check_quality import check_quality
from app.test.create_question import create_question


class Question(MongoEntry):
    question: str
    base_url: str
    link: str
    chunk_id: str


def _print(
        content: str,
        question: str
):
    print("***********************************")
    print("Content: ############################")
    print(content)
    print("Question: ############################")
    print(question)
    print("***********************************")


async def create_questions_flow(with_context: bool = True):
    mdb = await get_mongo_db()
    docs_chunks = await mdb.get_entries(DocsChunk, {"processed": True, "base_url": "https://docs.expo.dev"})
    visited = {question.chunk_id for question in await mdb.get_entries(Question, {"base_url": "https://docs.expo.dev"})}
    counter = 0

    while True:
        if counter == 100:
            break
        chunk: DocsChunk = random.choice(docs_chunks)

        if not with_context:
            context = await mdb.get_entry_from_col_value(
                column_name="chunk_id",
                column_value=chunk.id,
                class_type=DocsContext
            )
            if context:
                content = chunk.content.split(context.context)[1]
            else:
                content = chunk.content

            chunk.content = content

        pattern = r"^v\d+\.\d+\.\d+$"

        match = re.match(pattern, chunk.link)

        try:
            if not match and chunk.processed and chunk.id not in visited:
                quality_verdict = await check_quality(chunk.content)

                if quality_verdict == 'yes':
                    context = await _get_surrounding_context(chunk=chunk, mdb=mdb, context_len=50000)
                    question = await create_question(
                        chunk=chunk.content,
                        context=context,
                    )

                    _print(chunk.content, question)

                    await mdb.add_entry(Question(
                        question=question,
                        base_url=chunk.base_url,
                        link=chunk.link,
                        chunk_id=chunk.id
                    ))
                    counter += 1
                    await asyncio.sleep(1)

            visited.add(chunk.id)
        except Exception as e:
            print(e)

# asyncio.run(create_questions_flow())
