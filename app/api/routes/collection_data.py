from typing import Annotated, Optional

from fastapi import APIRouter, Depends

import logging

from pydantic import BaseModel

from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.models.docs import DocsContent

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

db_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]

class ContentDto(BaseModel):
    base_url:str
    link: str

@router.get("/get_all_content_data")
async def get_all_content_data(base_url: str,mdb: db_dep):
    entries = await mdb.get_entries(
        class_type=DocsContent,
        doc_filter={"base_url": base_url,},
    )
    return entries

@router.get("/get_content_data_by_link")
async def get_content_data_by_link(base_url:str, link: str,mdb: db_dep):
    entries = await mdb.get_entries(
        class_type=DocsContent,
        doc_filter={"base_url": base_url, "link": link},
    )
    print(entries)
    return entries
