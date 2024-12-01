import asyncio

from app.databases.mongo_db import MongoDBDatabase
from langchain_text_splitters import Language
from tqdm import tqdm
from app.models.preprocess import DocumentChunk, Content
from app.models.text_splitters import TextSplitter


async def chunk_docs():
    mdb = MongoDBDatabase()

    await mdb.delete_collection("DocumentationChunk")
    entries = await mdb.get_entries(Content)

    text_splitter = TextSplitter(
        language=Language.MARKDOWN,
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )

    for entry in tqdm(entries):
        content = entry.content
        content_id = entry.id

        texts = text_splitter.split_text(content)

        if len(texts) < 30:

            for i, text in enumerate(texts):
                doc_chunk = DocumentChunk(
                    content_id=content_id,
                    content=text[0],
                    start_index=text[1][0],
                    end_index=text[1][1],
                    order=i
                )
                await mdb.add_entry(doc_chunk)


# asyncio.run(chunk_docs())