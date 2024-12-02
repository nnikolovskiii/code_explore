from typing import Annotated

from fastapi import HTTPException, APIRouter, Depends

from app.code_process.pre_process.git_utils import clone_git_repo
from app.databases.mongo_db import MongoDBDatabase

import logging

from app.databases.singletons import get_mongo_db

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]

@router.get("/clone_library/")
async def clone_library(git_url: str,override: bool, mdb: mdb_dep):
    status, message = await clone_git_repo(mdb,git_url,override)
    return message