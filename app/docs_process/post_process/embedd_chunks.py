import logging
from typing import List

from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from tqdm import tqdm

from app.models.docs import DocsChunk, DocsContext, DocsEmbeddingFlag, Link
from app.models.process import create_process, increment_process, finish_process

logger = logging.getLogger(__name__)


async def create_final_chunks(
        mdb: MongoDBDatabase,
        chunks: List[DocsChunk],
        contexts: List[DocsContext]
):
    contexts_dict = {context.chunk_id: context.context for context in contexts}

    final_chunks = []

    count_context = 0
    count_all = 0
    for i,chunk in enumerate(chunks):
        content = chunk.content

        if chunk.id in contexts_dict:
            content = contexts_dict[chunk.id] + content
            count_context += 1

        chunk.content = content

        await mdb.update_entry(chunk)
        final_chunks.append(chunk)
        count_all += 1

    if len(chunks)>0:
        logger.info(f"{count_context / len(chunks) * 100:.2f}% of chunks had context added")
        logger.info(f"{count_all / len(chunks) * 100:.2f}% of chunks were successfully added to the database")

    return final_chunks

async def create_and_embedd_final_chunks_links(
        mdb: MongoDBDatabase,
        links: List[str],
        docs_url: str,
        qdb: QdrantDatabase,
):
    embedded_flags = await mdb.get_entries(DocsEmbeddingFlag, doc_filter={"base_url": docs_url})
    embedded_links = {flag.link for flag in embedded_flags}

    chunks = []
    contexts = []
    for link in links:
        if link not in embedded_links:
            link_chunks = await mdb.get_entries(DocsChunk, doc_filter={"link": link})
            chunks.extend(link_chunks)
            link_contexts = await mdb.get_entries(DocsContext, doc_filter={"link": link})
            contexts.extend(link_contexts)

    await create_final_chunks(mdb, chunks, contexts)
    await embedd_chunks(mdb, qdb, chunks)


async def embedd_chunks(
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase,
        chunks: List[DocsChunk],
):
    links_set = {chunk.link for chunk in chunks}
    process = await create_process(url = chunks[0].base_url,end = len(chunks),process_type = "embedd",mdb = mdb, type="docs")


    for i,chunk in enumerate(chunks):
        if i % 10 == 0:
            await increment_process(process, mdb, i)

        await qdb.embedd_and_upsert_record(
            value=chunk.content,
            entity=chunk,
            metadata={"active": True}
        )

    if len(chunks) > 0:
        for link in links_set:
            await mdb.add_entry(DocsEmbeddingFlag(
                base_url=chunks[0].base_url,
                link=link,
            ))
            folder = await mdb.get_entry_from_col_value(
                column_name="link",
                column_value=link,
                class_type=Link
            )

            folder.active = True

            await mdb.update_entry(
                folder
            )

    await finish_process(process, mdb)
