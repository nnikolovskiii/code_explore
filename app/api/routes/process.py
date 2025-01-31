from typing import Annotated

from bson import ObjectId
from fastapi import HTTPException, APIRouter, Depends

from app.databases.mongo_db import MongoDBDatabase

import logging

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.processstatus import ProcessStatus, create_process

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


@router.get("/get_finished_processes/")
async def get_finished_processes(group: str, mdb: mdb_dep):
    try:
        finished_processes = await mdb.get_entries(ProcessStatus, doc_filter={"finished": True, "group": group})

        return {"processes": finished_processes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_ongoing_processes/")
async def get_ongoing_processes(group: str, mdb: mdb_dep):
    try:
        ongoing_processes = await mdb.get_entries(ProcessStatus, doc_filter={"finished": False, "group": group})

        return {"processes": ongoing_processes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/refresh_progress/")
async def refresh_progress(process_id:str, mdb: mdb_dep):
    try:
        process = await mdb.get_entry(ObjectId(process_id), ProcessStatus)
        return process
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_processes_from_url/")
async def get_processes_from_url(url:str, group: str, mdb: mdb_dep):
    try:
        process_objs = await mdb.get_entries(ProcessStatus, doc_filter={"url": url, "group":group})
        process_dict = {process_obj.process_type: (process_obj.finished, process_obj.order) for process_obj in process_objs}
        return process_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_process/")
async def get_process(url:str, process_type:str, group: str, mdb: mdb_dep):
    try:
        process = await mdb.get_entry_from_col_values(
            columns={"url": url, "process_type": process_type, "group": group},
            class_type=ProcessStatus
        )
        return process
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/create_processes/")
async def create_processes(url:str, group:str, mdb: mdb_dep):
    try:
        await mdb.delete_entries(ProcessStatus, doc_filter={"url": url, "group": group})
        await create_process(
            url=url,
            mdb=mdb,
            process_type="main",
            type="docs",
            order=0,
            status="Started the process. Please refresh.",
            group="pre"
        )
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))