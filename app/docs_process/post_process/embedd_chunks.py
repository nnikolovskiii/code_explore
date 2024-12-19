import logging
from typing import List

from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase

from app.models.docs import DocsChunk, DocsContext, DocsEmbeddingFlag, Link
from app.models.process import create_process, increment_process, finish_process

logger = logging.getLogger(__name__)


async def embedd_chunks(
        mdb: MongoDBDatabase,
        links: List[str],
        docs_url: str,
        qdb: QdrantDatabase,
):
    process = await create_process(
        url=docs_url,
        end=await _get_embedd_chunks_length(links, mdb),
        process_type="embedd",
        mdb=mdb,
        type="docs"
    )

    count = 0
    for link in links:
        flag = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=DocsEmbeddingFlag
        )

        if flag is None:
            chunks = await mdb.get_entries(DocsChunk, doc_filter={"link": link})
            for chunk in chunks:
                await increment_process(process, mdb, count, 10)

                context = await mdb.get_entry_from_col_value(
                    column_name="chunk_id",
                    column_value=chunk.id,
                    class_type=DocsContext
                )
                if context is not None:
                    chunk.content = context.context + chunk.content

                try:
                    await qdb.embedd_and_upsert_record(
                        value=chunk.content,
                        entity=chunk,
                        metadata={"active": True}
                    )
                except Exception as e:
                    logging.error(e)

                count +=1

        await mdb.add_entry(DocsEmbeddingFlag(
            base_url=docs_url,
            link=link,
        ))

        link = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=Link
        )

        link.active = True
        await mdb.update_entry(link)

    await finish_process(process, mdb)

async def _get_embedd_chunks_length(links:List[str], mdb:MongoDBDatabase)->int:
    count = 0
    for link in links:
        flag = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=DocsEmbeddingFlag
        )

        if flag is None:
            count += await mdb.count_entries(DocsChunk, doc_filter={"link": link})
    return count