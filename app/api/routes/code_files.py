import asyncio
from typing import Annotated, List, Dict

from bson import ObjectId
from fastapi import HTTPException, APIRouter, Depends
from openai import BaseModel

from app.code_process.code_process_flow import change_active_files, FileActiveListDto
from app.databases.mongo_db import MongoDBDatabase, MongoEntry

import logging

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.code import CodeContent, CodeChunk, GitUrl, Folder, CodeContext, CodeEmbeddingFlag, CodeActiveFlag
from fastapi import WebSocket

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


class FileActiveDto(BaseModel):
    file_path: str
    active: bool


@router.get("/get_files/")
async def get_files(prev_folder: str, mdb: mdb_dep):
    folders = await mdb.get_entries(Folder, doc_filter={"prev": prev_folder})
    temp_folders = await mdb.get_entries(Folder, doc_filter={"prev": prev_folder}, collection_name="TempFolder")
    temp_folders_set = {folder.next for folder in temp_folders}
    temp_active_dict = {folder.next: folder.active for folder in temp_folders}

    for folder in folders:
        if folder.next in temp_folders_set:
            if not folder.active and temp_active_dict[folder.next]:
                folder.color = "green"
            elif folder.active and not temp_active_dict[folder.next]:
                folder.color = "red"
            elif folder.active and temp_active_dict[folder.next]:
                folder.color = "blue"
            else:
                folder.color = "white"
        else:
            if folder.active:
                folder.color = "blue"
            else:
                folder.color = "white"

    return {"folders": folders, }

@router.get("/activate_tmp_files/")
async def activate_tmp_files(git_url: str, mdb: mdb_dep, qdb: qdb_dep):
    folders = await mdb.get_entries(Folder, doc_filter={"url": git_url}, collection_name="TempFolder")
    folder_paths = [folder.next for folder in folders]
    active_status = [folder.active for folder in folders]

    await change_active_files(
        file_dto=FileActiveListDto(
            file_paths=folder_paths,
            active=active_status, ),
        git_url=git_url,
        mdb=mdb,
        qdb=qdb,
    )
    await mdb.delete_entries(Folder, doc_filter={"url": git_url}, collection_name="TempFolder")


@router.post("/update_file/")
async def update_file(file_active_dto: FileActiveDto, mdb: mdb_dep):
    tmp_folder = await mdb.get_entry_from_col_value(
        column_name="next",
        column_value=file_active_dto.file_path,
        class_type=Folder,
        collection_name="TempFolder",
    )
    if tmp_folder is None:
        folder = await mdb.get_entry_from_col_value(
            column_name="next",
            column_value=file_active_dto.file_path,
            class_type=Folder,
        )
        folder.active = file_active_dto.active
        await mdb.add_entry(folder, "TempFolder")
    else:
        tmp_folder.active = file_active_dto.active
        await mdb.update_entry(tmp_folder, "TempFolder")

@router.get("/get_git_urls/")
async def get_git_urls(mdb: mdb_dep):
    try:
        git_urls = await mdb.get_entries(GitUrl)
        return {"git_urls": git_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
