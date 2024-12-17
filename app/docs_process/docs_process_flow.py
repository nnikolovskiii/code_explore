import asyncio
from typing import List

from pydantic import BaseModel

from app.code_process.post_process.active_status import update_records
from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from app.docs_process.post_process.add_context import add_context_links
from app.docs_process.post_process.embedd_chunks import create_and_embedd_final_chunks_links
from app.docs_process.pre_process.chunking import chunk_links
from app.models.docs import Link


class DocsActiveListDto(BaseModel):
    links: List[str]
    active: List[bool]


async def process_code_files(
        links: List[str],
        docs_url: str,
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase,
):
    await chunk_links(links=links, docs_url=docs_url, mdb=mdb)
    await add_context_links(mdb=mdb, links=links, docs_url=docs_url)
    await create_and_embedd_final_chunks_links(mdb=mdb, qdb=qdb, links=links, docs_url=docs_url)


async def change_active_files(
        docs_dto: DocsActiveListDto,
        docs_url: str,
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase
):
    await process_code_files(
        links=docs_dto.links,
        docs_url=docs_url,
        mdb=mdb,
        qdb=qdb,
    )

    for link, active_status in zip(docs_dto.links, docs_dto.active):
        docs_active_flag = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=Link,
        )

        docs_active_flag.active = active_status
        await mdb.update_entry(docs_active_flag)

        record = await update_records(
            qdb=qdb,
            collection_name="DocsChunk",
            filter={("link", "value"): link},
            update={"active": active_status},
        )

#
# asyncio.run(change_active_files(
#     DocsActiveListDto(
#         links=["https://fastapi.tiangolo.com/tutorial/body"],
#         active=[True]
#     ),
#     docs_url="https://fastapi.tiangolo.com/",
#     mdb=MongoDBDatabase(),
#     qdb=QdrantDatabase(),
# ))
