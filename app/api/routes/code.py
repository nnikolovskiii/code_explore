from typing import Annotated, List

from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel

from app.code_process.post_process.add_context import add_context_files, add_context_all
from app.code_process.post_process.embedd_chunks import create_final_chunks_all_code, create_final_chunks_files, \
    embedd_chunks_all_code, embedd_chunks_files
from app.code_process.pre_process.extract_content import extract_contents, chunk_code, chunk_files, chunk_all_code
from app.code_process.pre_process.git_utils import clone_git_repo
from app.databases.mongo_db import MongoDBDatabase

import logging
import shutil

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.code import CodeContent, CodeChunk, GitUrl, Folder, CodeContext

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]

class FileDto(BaseModel):
    file_paths: List[str]

@router.get("/extract_library/")
async def extract_library(git_url: str,override: bool, mdb: mdb_dep, qdb: qdb_dep):
    try:
        if override:
            await mdb.delete_entries(CodeContent, doc_filter={"url": git_url})
            await mdb.delete_entries(CodeChunk, doc_filter={"url": git_url})
            await mdb.delete_entries(GitUrl, doc_filter={"url": git_url})
            await mdb.delete_entries(CodeContext, doc_filter={"url": git_url})
            await mdb.delete_entries(Folder, doc_filter={"url": git_url})

        urls = await mdb.get_entries(GitUrl, doc_filter={"url": git_url})
        if len(urls) == 0:
            await mdb.add_entry(GitUrl(url=git_url))
            folder_path = await clone_git_repo(mdb,git_url,override)
            print(folder_path)
            await extract_contents(folder_path, git_url)
            shutil.rmtree(folder_path)
            return {"status": "success", "message": "Library cloned and processed successfully."}
        else:
            return {"status": "success", "message": "Library is already cloned"}
    except Exception as e:
        logging.exception("Error cloning library")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chunk_all_code/")
async def _chunk_all_code(git_url: str, mdb: mdb_dep, qdb: qdb_dep):
    await chunk_all_code(git_url=git_url, mdb=mdb)
    await add_context_all(mdb=mdb, git_url=git_url)
    await create_final_chunks_all_code(mdb=mdb, git_url=git_url)
    await embedd_chunks_all_code(mdb=mdb, qdb=qdb, git_url=git_url)

@router.post("/chunk_files/")
async def _chunk_files(file_dto: FileDto, git_url: str, mdb: mdb_dep, qdb: qdb_dep):
    await chunk_files(file_paths=file_dto.file_paths, git_url=git_url, mdb=mdb)
    await add_context_files(mdb=mdb, file_paths=file_dto.file_paths)
    await create_final_chunks_files(mdb=mdb, file_paths=file_dto.file_paths)
    await embedd_chunks_files(mdb=mdb, qdb=qdb, file_paths=file_dto.file_paths)

@router.get("/get_files/")
async def get_files(prev_folder: str, mdb: mdb_dep):
    folders = await mdb.get_entries(Folder, doc_filter={"prev": prev_folder})

    return {"folders": folders,}

