import asyncio

from bson import ObjectId

from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.docs import FinalDocumentChunk, DocumentChunk, Context, Category, Content
from tqdm import tqdm

async def create_final_chunks():
    mdb = await get_mongo_db()
    chunks = await mdb.get_entries(DocumentChunk)

    url_dict = {}
    for chunk in chunks:
        content = await mdb.get_entity(id = ObjectId(chunk.content_id), class_type=Content)
        url_dict[chunk.id] = content.link

    contexts = await mdb.get_entries(Context)
    contexts_dict = {context.chunk_id: context.context for context in contexts}
    categories = await mdb.get_entries(Category)
    categories_dict = {category.chunk_id: category.name for category in categories}

    count=0
    count1 = 0
    for chunk in tqdm(chunks, total=50):
        new_dict = {"chunk_id": chunk.id, "content": chunk.content, "link": url_dict[chunk.id]}

        if chunk.id in contexts_dict:
            new_dict["content"] = contexts_dict[chunk.id] + new_dict["content"]
            count+=1
        if chunk.id in categories_dict:
            new_dict["category"] = categories_dict[chunk.id]
            final_chunk = FinalDocumentChunk(**new_dict)
            await mdb.add_entry(final_chunk)
            count1 += 1

    print(count/len(chunks)*100)
    print(count1/len(chunks)*100)


async def embedd_chunks():
    mdb = await get_mongo_db()
    qdb = await get_qdrant_db()

    final_chunks = await mdb.get_entries(FinalDocumentChunk)

    for chunk in tqdm(final_chunks):
        await qdb.embedd_and_upsert_record(
            value=chunk.content,
            entity=chunk
        )

asyncio.run(embedd_chunks())