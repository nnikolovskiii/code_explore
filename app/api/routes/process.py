from typing import Annotated

from bson import ObjectId
from fastapi import HTTPException, APIRouter, Depends

from app.databases.mongo_db import MongoDBDatabase

import logging

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.process import Process
from app.models.simple_process import SimpleProcess

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


@router.get("/get_finished_processes/")
async def get_finished_processes(mdb: mdb_dep):
    try:
        finished_processes = await mdb.get_entries(Process, doc_filter={"finished": True,})

        return {"processes": finished_processes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_ongoing_processes/")
async def get_ongoing_processes(mdb: mdb_dep):
    try:
        ongoing_processes = await mdb.get_entries(Process, doc_filter={"finished": False,})

        return {"processes": ongoing_processes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/refresh_progress/")
async def refresh_progress(process_id:str, mdb: mdb_dep):
    try:
        process = await mdb.get_entry(ObjectId(process_id), Process)
        return process
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_pre_processes/")
async def get_pre_processes(url:str, mdb: mdb_dep):
    try:
        process_objs = await mdb.get_entries(SimpleProcess, doc_filter={"url": url})
        process_dict = {process_obj.process_type: (process_obj.finished, process_obj.order) for process_obj in process_objs}
        return process_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))