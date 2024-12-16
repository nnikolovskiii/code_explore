from typing import List

from app.databases.mongo_db import MongoDBDatabase
from langchain_text_splitters import Language
from tqdm import tqdm
from app.models.docs import DocsChunk, DocsEmbeddingFlag, DocsContent
from app.models.splitters.text_splitters import TextSplitter


async def chunk_docs(
        mdb: MongoDBDatabase,
        docs_contents: List[DocsContent],
):
    text_splitter = TextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )

    separators = text_splitter.get_separators_for_language(Language.MARKDOWN,)
    text_splitter._separators = separators

    for content in tqdm(docs_contents):
        texts = text_splitter.split_text(content.content)

        # Important: change later
        if len(texts) < 30:
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
    embedded_flags = await mdb.get_entries(DocsEmbeddingFlag, doc_filter={"base_url": docs_url})
    embedded_links = {flag.link for flag in embedded_flags}

    contents = []
    for link in links:
        if link not in embedded_links:
            content = await mdb.get_entry_from_col_value(
                column_name="link",
                column_value=link,
                class_type=DocsContent
            )
            contents.append(content)
    await chunk_docs(mdb, contents)
