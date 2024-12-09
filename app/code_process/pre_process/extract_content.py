import asyncio
import os
from typing import List

from bson import ObjectId
from datasets import tqdm
from dotenv import load_dotenv

from app.code_process.pre_process.file_utils import _get_all_file_paths, _get_file_extension, _read_file
from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.models.code import CodeContent, CodeChunk, Folder, CodeEmbeddingFlag
from app.models.splitters.base_splitter import Language
from app.models.splitters.text_splitters import TextSplitter


async def extract_contents(folder_path: str, git_url: str):
    mdb = await get_mongo_db()
    file_paths = _get_all_file_paths(folder_path)

    load_dotenv()
    root_git_path = os.getenv("ROOT_GIT_PATH")

    s = set()

    for file_path in tqdm(file_paths):
        try:
            extension = _get_file_extension(file_path)
            content = _read_file(file_path)
            no_root_path = file_path.split(root_git_path)[1]
            file_name = no_root_path.split("/")[-1]
            folder_path = no_root_path.split("/"+file_name)[0]

            folders = folder_path.split("/")
            acc_folder = folders[0]
            for folder in folders[1:]:
                s.add((acc_folder, acc_folder+"/"+folder))
                acc_folder+="/"+folder

            if extension:
                await mdb.add_entry(CodeContent(
                    url=git_url,
                    file_path=no_root_path,
                    content= content,
                    extension= extension
                ))

                await mdb.add_entry(Folder(
                    url=git_url,
                    prev=folder_path,
                    next=no_root_path,
                    is_folder=False
                ))

        except Exception as e:
            print(e)

    for prev_folder, next_folder in s:
        folder = Folder(
            url=git_url,
            prev=prev_folder,
            next=next_folder,
            is_folder=True
        )
        await mdb.add_entry(folder)


async def chunk_code(
        mdb: MongoDBDatabase,
        code_contents: List[CodeContent],
)->List[CodeChunk]:
    text_splitter = TextSplitter(
        language=Language.PYTHON,
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )

    chunks = []

    for content in tqdm(code_contents):
        if content.extension == ".py":
            texts = text_splitter.split_text(content.content)

            for i, text in enumerate(texts):
                code_chunk = CodeChunk(
                    url=content.url,
                    file_path=content.file_path,
                    content_id=content.id,
                    content=text[0],
                    start_index=text[1][0],
                    end_index=text[1][1],
                    order=i,
                    code_len=len(texts)
                )
                code_chunk.id = await mdb.add_entry(code_chunk)
                chunks.append(code_chunk)

    return chunks


async def chunk_all_code(
        mdb: MongoDBDatabase,
        git_url: str,
)->List[CodeChunk]:
    contents = await mdb.get_entries(CodeContent, doc_filter={"url": git_url})
    return await chunk_code(mdb, contents)

async def chunk_files(
        mdb: MongoDBDatabase,
        file_paths: List[str],
        git_url: str,
)->List[CodeChunk]:
    embedded_flags = await mdb.get_entries(CodeEmbeddingFlag, doc_filter={"url": git_url})
    embedded_files = {flag.file_path for flag in embedded_flags}
    print(embedded_files)

    contents = []
    for file_path in file_paths:
        if file_path not in embedded_files:
            content = await mdb.get_entry_from_col_value(
                column_name="file_path",
                column_value=file_path,
                class_type = CodeContent
            )
            contents.append(content)
    return await chunk_code(mdb, contents)