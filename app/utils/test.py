import asyncio

from app.databases.singletons import get_mongo_db
from app.models.docs import DocsChunk, DocsEmbeddingFlag, DocsContent, DocsContext


async def lol():
    mdb = await get_mongo_db()
    # await mdb.create_index("link", DocsChunk)
    # await mdb.create_index("link", DocsEmbeddingFlag)
    # await mdb.create_index("link", DocsContent)
    await mdb.create_index("chunk_id", DocsContext)


asyncio.run(lol())