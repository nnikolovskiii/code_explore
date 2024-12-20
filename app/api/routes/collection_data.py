from typing import Annotated

from fastapi import APIRouter, Depends

import logging

from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.models.docs import DocsContent

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

db_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]

@router.get("/")
async def get_collection_data(collection_name: str ,mdb: db_dep):
    print("lol")
    entries = await mdb.get_entries(class_type=DocsContent,collection_name=collection_name, doc_filter={"base_url": "https://huggingface.co/docs"})
    print(len(entries))
    return entries
