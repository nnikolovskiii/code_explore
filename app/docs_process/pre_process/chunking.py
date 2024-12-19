import logging
from typing import List

from app.databases.mongo_db import MongoDBDatabase
from langchain_text_splitters import Language
from app.models.docs import DocsChunk, DocsEmbeddingFlag, DocsContent
from app.models.process import create_process, increment_process, finish_process
from app.models.splitters.text_splitters import TextSplitter


async def chunk_content(
        mdb: MongoDBDatabase,
        content: DocsContent,
        text_splitter: TextSplitter,
        huge_content: bool = False
):
    texts = text_splitter.split_text(content.content)

    # Important: change later
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
        links: List[str],
        docs_url: str,
):
    text_splitter = TextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )

    separators = text_splitter.get_separators_for_language(Language.MARKDOWN, )
    text_splitter._separators = separators

    process = await create_process(
        url=docs_url,
        end=await _get_chunk_links_length(links, mdb),
        process_type="chunk",
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

        chunk = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=DocsChunk
        )

        if chunk is None and flag is None:
            await increment_process(process, mdb, count, 10)
            content = await mdb.get_entry_from_col_value(
                column_name="link",
                column_value=link,
                class_type=DocsContent
            )
            try:
                await chunk_content(mdb, content, text_splitter, True)
            except Exception as e:
                logging.error(e)
            count+=1
    await finish_process(process, mdb)


async def _get_chunk_links_length(links:List[str], mdb: MongoDBDatabase) -> int:
    count = 0
    for link in links:
        flag = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=DocsEmbeddingFlag
        )

        chunk = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=DocsChunk
        )

        if chunk is None and flag is None:
            count += 1

    return count
