import asyncio
import os

from datasets import tqdm
from dotenv import load_dotenv

from app.code_process.pre_process.file_utils import _get_all_file_paths, _get_file_extension, _read_file
from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.models.code import CodeContent, CodeChunk, Folder
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
                s.add((acc_folder, folder))
                acc_folder+="/"+folder

            if extension:
                await mdb.add_entry(CodeContent(
                    url=git_url,
                    file_path=no_root_path,
                    content= content,
                    extension= extension
                ))

                await mdb.add_entry(Folder(
                    git_url=git_url,
                    prev=folder_path,
                    next=no_root_path,
                    is_folder=False
                ))

        except Exception as e:
            print(e)

    for prev_folder, next_folder in s:
        folder = Folder(
            git_url=git_url,
            prev=prev_folder,
            next=next_folder,
            is_folder=True
        )
        await mdb.add_entry(folder)

async def chunk_code(git_url: str, mdb: MongoDBDatabase):
    code_contents = await mdb.get_entries(CodeContent, doc_filter={"url": git_url})
    files = await mdb.get_entries(Folder, doc_filter={"url": git_url, "is_folder": False})
    files_dict = {file.next:file for file in files}

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
                    url=content.url,
                    content_id=content.id,
                    content=text[0],
                    start_index=text[1][0],
                    end_index=text[1][1],
                    order=i,
                    code_len=len(texts)
                )
                await mdb.add_entry(code_chunk)
            content.embedded = True
            await mdb.update_entry(content)

        file = files_dict[content.file_path]
        file.embedded = True
        await mdb.update_entry(file)