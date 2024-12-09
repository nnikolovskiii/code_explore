from typing import Annotated, List

from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel

from app.code_process.code_process_flow import process_code_files
from app.code_process.post_process.active_status import update_records
from app.code_process.post_process.add_context import add_context_chunks
from app.code_process.post_process.embedd_chunks import create_final_chunks, embedd_chunks
from app.code_process.pre_process.extract_content import extract_contents, chunk_code, chunk_files, chunk_all_code
from app.code_process.pre_process.git_utils import clone_git_repo
from app.databases.mongo_db import MongoDBDatabase

import logging
import shutil

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.code import CodeContent, CodeChunk, GitUrl, Folder, CodeContext, CodeEmbeddingFlag, CodeActiveFlag

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


@router.get("/get_files/")
async def get_files(prev_folder: str, mdb: mdb_dep):
    folders = await mdb.get_entries(Folder, doc_filter={"prev": prev_folder})

    return {"folders": folders, }


