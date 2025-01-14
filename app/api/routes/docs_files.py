from typing import Annotated, List, Dict

from fastapi import HTTPException, APIRouter, Depends
from openai import BaseModel

from app.databases.mongo_db import MongoDBDatabase, MongoEntry

import logging

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.docs_process.docs_post_process_flow import change_active_files, DocsActiveListDto

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

    return {"links": links, }

@router.get("/activate_tmp_files/")
async def activate_tmp_files(docs_url: str, mdb: mdb_dep, qdb: qdb_dep):
    await change_active_files(
        docs_url=docs_url,
        mdb=mdb,
        qdb=qdb,
    )
    await mdb.delete_entries(Link, doc_filter={"base_url": docs_url}, collection_name="TempLink")


@router.post("/update_link/")
async def update_link(docs_active_dto: DocsActiveDto, mdb: mdb_dep):
    await add_update_tmp_link(docs_active_dto.link, docs_active_dto.active, mdb)

@router.get("/get_docs_urls/")
async def get_git_urls(mdb: mdb_dep):
    try:
        docs_urls = await mdb.get_entries(DocsUrl)
        return {"docs_urls": docs_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/select_all_links/")
async def select_all_links(prev_link: str, select:bool, mdb: mdb_dep):
    links = await mdb.get_entries(Link, doc_filter={"prev_link": prev_link})
    while len(links) > 0:
        link = links.pop()
        await add_update_tmp_link(link.link, select, mdb)
        links.extend(await mdb.get_entries(Link, doc_filter={"prev_link": link.link}))


    return {"links": links, }

@router.get("/select_docs/")
async def select_docs(docs_url:str, select:bool, mdb: mdb_dep):
    links = await mdb.get_entries(Link, doc_filter={"base_url": docs_url})
    for link in links:
        await add_update_tmp_link(link.link, select, mdb)

    return {"links": links, }

async def add_update_tmp_link(link:str,active:bool,mdb:MongoDBDatabase):
    tmp_link = await mdb.get_entry_from_col_value(
        column_name="link",
        column_value=link,
        class_type=Link,
        collection_name="TempLink",
    )
    if tmp_link is None:
        link = await mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link,
            class_type=Link,
        )
        link.active = active
        await mdb.add_entry(link, "TempLink")
    else:
        tmp_link.active = active
        await mdb.update_entry(tmp_link, "TempLink")

class DocsUrlDto(BaseModel):
    docs_urls: List[str]
    active: List[bool]

@router.post("/change_active_repos/")
async def change_active_repos(docs_url_dto: DocsUrlDto ,mdb: mdb_dep):
    for docs_url, active_status in zip(docs_url_dto.docs_urls, docs_url_dto.active):
        docs_url_obj = await mdb.get_entry_from_col_value(
            column_name="url",
            column_value=docs_url,
            class_type=DocsUrl
        )
        docs_url_obj.active = active_status
        await mdb.update_entry(docs_url_obj)