import logging
from typing import List

from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from langchain_text_splitters import Language
from app.models.docs import DocsChunk, DocsEmbeddingFlag, DocsContent, Link
from app.models.process import create_process, increment_process, finish_process, Process
from app.models.splitters.text_splitters import TextSplitter

class ChunkLink(MongoEntry):
    link: str
    url:str


async def chunk_content(
        mdb: MongoDBDatabase,
        content: DocsContent,
        text_splitter: TextSplitter,
        huge_content: bool = False
):
    texts = text_splitter.split_text(content.content)

    if huge_content or (len(texts) < 50 and not huge_content):
        for i, text in enumerate(texts):
            doc_chunk = DocsChunk(
                base_url=content.base_url,
                link=content.link,
                content_id=content.id,
                content=text[0],
                start_index=int(text[1][0]),
                end_index=int(text[1][1]),
                order=i,
                doc_len=len(texts)
            )
            await mdb.add_entry(doc_chunk)


async def chunk_links(
        mdb: MongoDBDatabase,
        docs_url: str,
):
    text_splitter = TextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )

    separators = text_splitter.get_separators_for_language(Language.MARKDOWN, )
    text_splitter._separators = separators

    process = await _get_chunk_links_length(docs_url, mdb)

    count = 0
    async for chunk_link in mdb.stream_entries(
        class_type=ChunkLink,
        doc_filter={"url": docs_url}
    ):
        await increment_process(process, mdb, count, 10)

        content = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=chunk_link.link,
            class_type=DocsContent
        )
        try:
            await chunk_content(mdb, content, text_splitter, True)
        except Exception as e:
            logging.error(e)
        count += 1

    await finish_process(process, mdb)

    await mdb.delete_entries(
        class_type=ChunkLink,
        doc_filter={"url": docs_url})


async def _get_chunk_links_length(docs_url: str, mdb: MongoDBDatabase) -> Process:
    count = 0
    await mdb.delete_entries(
        class_type=ChunkLink,
        doc_filter={"url": docs_url})

    async for link_obj in mdb.stream_entries(
            class_type=Link,
            doc_filter={"base_url": docs_url, "processed": False,},
            collection_name="TempLink"
    ):
        exist_one_chunk = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link_obj.link,
            class_type=DocsChunk
        )
        if exist_one_chunk is None:
            await mdb.add_entry(ChunkLink(link=link_obj.link, url=docs_url))
            count += 1

    process = await create_process(
        url=docs_url,
        end=count,
        process_type="chunk",
        mdb=mdb,
        type="docs"
    )

    return process