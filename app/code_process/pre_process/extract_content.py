import asyncio

from datasets import tqdm

from app.code_process.pre_process.file_utils import _get_all_file_paths, _get_file_extension, _read_file
from app.databases.singletons import get_mongo_db
from app.models.code import CodeContent, CodeChunk
from app.models.splitters.base_splitter import Language
from app.models.splitters.text_splitters import TextSplitter


async def extract_contents(folder_path: str):
    mdb = await get_mongo_db()
    file_paths = _get_all_file_paths(folder_path)

    for file_path in tqdm(file_paths):
        try:
            extension = _get_file_extension(file_path)
            content = _read_file(file_path)
            if extension:
                await mdb.add_entry(CodeContent(
                    file_path=file_path,
                    content= content,
                    extension= extension
                ))

        except Exception as e:
            print(e)

async def chunk_code():
    mdb = await get_mongo_db()
    await mdb.delete_collection("CodeChunk")
    code_contents = await mdb.get_entries(CodeContent)

    text_splitter = TextSplitter(
        language=Language.PYTHON,
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )

    for content in tqdm(code_contents):
        if content.extension == ".py":
            texts = text_splitter.split_text(content.content)

            for i, text in enumerate(texts):
                code_chunk = CodeChunk(
                    content_id=content.id,
                    content=text[0],
                    start_index=text[1][0],
                    end_index=text[1][1],
                    order=i,
                    file_path=content.file_path,
                    code_len=len(texts)
                )
                await mdb.add_entry(code_chunk)


asyncio.run(chunk_code())