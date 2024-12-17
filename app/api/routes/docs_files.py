from typing import Annotated, List, Dict

from fastapi import HTTPException, APIRouter, Depends
from openai import BaseModel

from app.databases.mongo_db import MongoDBDatabase, MongoEntry

import logging

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.docs_process.docs_process_flow import change_active_files, DocsActiveListDto

from app.models.docs import Link, DocsUrl

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


class DocsActiveDto(BaseModel):
    link: str
    active: bool


@router.get("/get_links/")
async def get_links(prev_link: str, mdb: mdb_dep):
    links = await mdb.get_entries(Link, doc_filter={"prev_link": prev_link})
    temp_links= await mdb.get_entries(Link, doc_filter={"prev_link": prev_link}, collection_name="TempLink")
    temp_links_set = {link.link for link in temp_links}
    temp_active_dict = {link.link: link.active for link in temp_links}

    for link in links:
        if link.link in temp_links_set:
            if not link.active and temp_active_dict[link.link]:
                link.color = "green"
            elif link.active and not temp_active_dict[link.link]:
                link.color = "red"
            elif link.active and temp_active_dict[link.link]:
                link.color = "blue"
            else:
                link.color = "white"
        else:
            if link.active:
                link.color = "blue"
            else:
                link.color = "white"

    return {"folders": links, }

@router.get("/activate_tmp_files/")
async def activate_tmp_files(docs_url: str, mdb: mdb_dep, qdb: qdb_dep):
    links = await mdb.get_entries(Link, doc_filter={"base_url": docs_url}, collection_name="TempLink")
    link_strs = [link.link for link in links]
    active_status = [link.active for link in links]

    await change_active_files(
        docs_dto=DocsActiveListDto(
            links=link_strs,
            active=active_status, ),
        docs_url=docs_url,
        mdb=mdb,
        qdb=qdb,
    )
    await mdb.delete_entries(Link, doc_filter={"base_url": docs_url}, collection_name="TempLink")


@router.post("/update_link/")
async def update_link(docs_active_dto: DocsActiveDto, mdb: mdb_dep):
    tmp_link = await mdb.get_entry_from_col_value(
        column_name="link",
        column_value=docs_active_dto.link,
        class_type=Link,
        collection_name="TempLink",
    )
    if tmp_link is None:
        link = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=docs_active_dto.link,
            class_type=Link,
        )
        link.active = docs_active_dto.active
        await mdb.add_entry(link, "TempLink")
    else:
        tmp_link.active = docs_active_dto.active
        await mdb.update_entry(tmp_link, "TempLink")

@router.get("/get_docs_urls/")
async def get_git_urls(mdb: mdb_dep):
    try:
        docs_urls = await mdb.get_entries(DocsUrl)
        return {"docs_urls": docs_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
