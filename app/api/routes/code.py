from typing import Annotated

from fastapi import HTTPException, APIRouter, Depends

from app.code_process.pre_process.extract_content import extract_contents
from app.code_process.pre_process.git_utils import clone_git_repo
from app.databases.mongo_db import MongoDBDatabase

import logging
import shutil

from app.databases.singletons import get_mongo_db
from app.models.code import CodeContent, CodeChunk, FinalCodeChunk, GitUrl

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]

@router.get("/extract_library/")
async def extract_library(git_url: str,override: bool, mdb: mdb_dep):
    try:
        if override:
            await mdb.delete_entries(CodeContent, doc_filter={"url": git_url})
            await mdb.delete_entries(CodeChunk, doc_filter={"url": git_url})
            await mdb.delete_entries(FinalCodeChunk, doc_filter={"url": git_url})
            await mdb.delete_entries(GitUrl, doc_filter={"url": git_url})

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
