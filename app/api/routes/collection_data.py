from typing import Annotated

from fastapi import HTTPException, APIRouter, Body, Depends

import logging

from app.databases.mongo.singleton import get_db

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

db_dep = Annotated[dict, Depends(get_db)]

@router.get("/")
async def get_collection_data(collection_name: str ,mdb: db_dep):
    entries = await mdb.get_entries_dict(collection_name)
    return entries
