from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends

from app.databases.mongo_db import MongoDBDatabase

import logging

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.flag import Flag

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


@router.get("/get_flag/")
async def get_flag(name:str, mdb: mdb_dep):
    flag_obj = await mdb.get_entry_from_col_value(
        column_name="name",
        column_value=name,
        class_type=Flag
    )

    if not flag_obj:
        flag_id = await mdb.add_entry(Flag(name=name, active=False))
        flag_obj = await mdb.get_entry(ObjectId(flag_id), Flag)
    return flag_obj


@router.get("/set_flag/")
async def set_flag(name:str, active: bool, mdb: mdb_dep):
    flag_obj = await mdb.get_entry_from_col_value(
        column_name="name",
        column_value=name,
        class_type=Flag
    )

    if not flag_obj:
        flag_id = await mdb.add_entry(Flag(name=name, active=active))
        flag_obj = await mdb.get_entry(ObjectId(flag_id), Flag)
    else:
        flag_obj.active = active
        await mdb.update_entry(flag_obj)
    return flag_obj
