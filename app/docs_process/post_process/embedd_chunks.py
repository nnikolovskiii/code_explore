from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.preprocess import FinalDocumentChunk
from tqdm import tqdm


async def embedd_chunks():
    mdb = await get_mongo_db()
    qdb = await get_qdrant_db()

    final_chunks = await mdb.get_entries(FinalDocumentChunk)

    for chunk in tqdm(final_chunks):
        await qdb.embedd_and_upsert_record(
            value=chunk.content,
            entity=chunk
        )
