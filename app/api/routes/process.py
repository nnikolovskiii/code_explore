from typing import Annotated

from fastapi import HTTPException, APIRouter, Depends

from app.databases.mongo_db import MongoDBDatabase

import logging

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.process import Process

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


@router.get("/get_processes/")
async def get_git_urls(mdb: mdb_dep):
    try:
        docs_processes_ongoing = await mdb.get_entries(Process, doc_filter={"finished": False, "type": "docs"})
        code_processes_ongoing = await mdb.get_entries(Process, doc_filter={"finished": False, "type": "code"})
        docs_processes_finished = await mdb.get_entries(Process, doc_filter={"finished": True, "type": "docs"})
        code_processes_finished = await mdb.get_entries(Process, doc_filter={"finished": True, "type": "code"})

        return {"code_processes_ongoing": code_processes_ongoing,
                "docs_processes_ongoing": docs_processes_ongoing,
                "code_processes_finished": code_processes_finished,
                "docs_processes_finished": docs_processes_finished}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
