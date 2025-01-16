import asyncio

import logging
from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from app.databases.qdrant_db import QdrantDatabase
from tqdm import tqdm

from app.models.docs import DocsChunk, DocsContext

logger = logging.getLogger(__name__)


class EmbeddChunk(MongoEntry):
    chunk_id: str
    url: str
    link: str


async def embedd_chunks(
        docs_url: str,
):
    mdb = MongoDBDatabase(url="mkpatka.duckdns.org")
    qdb = QdrantDatabase(url="localhost")
    existing_ids = {obj.my_id for obj in await mdb.get_entries(Metadata)}

    chunks = await mdb.get_entries(
            class_type=DocsChunk,
            doc_filter={"base_url": docs_url}
    )

    filtered_chunks = [chunk for chunk in chunks if chunk.id not in existing_ids]

    for chunk in tqdm(filtered_chunks):
        if chunk.id in existing_ids:
            continue
        try:
            context = await mdb.get_entry_from_col_value(
                column_name="chunk_id",
                column_value=chunk.id,
                class_type=DocsContext
            )

            content = chunk.content.split(context.context)[1]
            content = content.strip()

            await qdb.embedd_and_upsert_record(
                value=content,
                entity=chunk,
                metadata={"active": False}
            )

            await mdb.add_entry(Metadata(my_id=chunk.id))
        except Exception as e:
            logging.error(e)




async def process_code_files(
        docs_url: str,
):
    await embedd_chunks(docs_url=docs_url)

async def count_chunks(url):
    mdb = MongoDBDatabase(url="mkpatka.duckdns.org")
    print(await mdb.count_entries(DocsChunk, doc_filter={"base_url": url}))

class Metadata(MongoEntry):
    my_id: str

async def save_ids_from_qdrant():
    mdb = MongoDBDatabase(url="mkpatka.duckdns.org")
    qdb = QdrantDatabase(url="localhost")
    ids = set()

    async for responses in qdb.scroll(collection_name="DocsChunk"):
        for response in responses:
            ids.add(response.payload["id"])

    for id in ids:
        await mdb.add_entry(Metadata(my_id=id))

# asyncio.run(save_ids_from_qdrant())
asyncio.run(process_code_files("https://docs.expo.dev"))
