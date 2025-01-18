from typing import Annotated, List, Set

from fastapi import APIRouter, Depends
from openai import BaseModel

from app.utils.qdrant_utils import update_records
from app.databases.mongo_db import MongoDBDatabase

import logging

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.docs_process.post_process.post_process import process_links_flow

from app.models.docs import Link

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


class DocsActiveDto(BaseModel):
    link: str
    active: bool


@router.get("/get_links_from_parent/")
async def get_links_from_parent(prev_link: str, mdb: mdb_dep):
    parent_links = await mdb.get_entries(Link, doc_filter={"prev_link": prev_link, "is_parent": True})
    child_links = await mdb.get_entries(Link, doc_filter={"prev_link": prev_link, "is_parent": False})
    child_links = sorted(child_links, key=lambda link: link.link)

    links = parent_links + child_links

    for link in links:
        if link.processed:
            link.color = "blue"
        else:
            link.color = "white"

        if link.active and not link.processed:
            link.color = "green"

    return {"links": links, }


@router.get("/process_links/")
async def process_links(docs_url: str, mdb: mdb_dep, qdb: qdb_dep):
    await process_links_flow(
        docs_url=docs_url,
        mdb=mdb,
        qdb=qdb,
    )

@router.get("/activate_link/")
async def activate_link(link:str, active_status:bool, mdb: mdb_dep, qdb: qdb_dep):
    link_obj = await mdb.get_entry_from_col_value(
        column_name="link",
        column_value=link,
        class_type=Link
    )
    link_obj.active = active_status
    await _update_links_qdrant(qdb=qdb,links={link_obj.link}, active_status=link_obj.active)

    await mdb.update_entry(link_obj)


@router.get("/activate_all_links_from_parent_recursively/")
async def activate_all_links_from_parent_recursively(prev_link: str, active_status: bool, mdb: mdb_dep, qdb: qdb_dep):
    link_obj = await mdb.get_entry_from_col_value(
        column_name="link",
        column_value=prev_link,
        class_type=Link
    )

    links_set: Set[str] = set()

    if link_obj:
        link_obj.active = active_status
        await mdb.update_entry(link_obj)
        links_set.add(link_obj.link)

    links = await mdb.get_entries(Link, doc_filter={"prev_link": prev_link})
    while len(links) > 0:
        link = links.pop()
        link.active = active_status
        await mdb.update_entry(link)
        links.extend(await mdb.get_entries(Link, doc_filter={"prev_link": link.link}))
        links_set.add(link_obj.link)

    await _update_links_qdrant(qdb=qdb, links=links_set, active_status=active_status)


@router.get("/activate_all_links_from_docs_url/")
async def activate_all_links_from_docs_url(docs_url: str, active_status: bool, mdb: mdb_dep, qdb: qdb_dep):
    links = await mdb.get_entries(Link, doc_filter={"base_url": docs_url})
    links_set: Set[str] = set()

    for link in links:
        link.active = active_status
        await mdb.update_entry(link)
        links_set.add(link.link)

    await _update_links_qdrant(qdb=qdb, links=links_set, active_status=active_status)


@router.get("/activate_all_links_from_parent/")
async def activate_all_links_from_parent(prev_link: str, active_status: bool, mdb: mdb_dep, qdb: qdb_dep):
    links = await mdb.get_entries(Link, doc_filter={"prev_link": prev_link})
    links_set: Set[str] = set()
    for link in links:
        link.active = active_status
        await mdb.update_entry(link)
        links_set.add(link.link)

    await _update_links_qdrant(qdb=qdb, links=links_set, active_status=active_status)



async def _update_links_qdrant(
        qdb: QdrantDatabase,
        links: Set[str],
        active_status: bool,
):
    await update_records(
        qdb=qdb,
        collection_name="DocsChunk",
        filter={("link", "any"): list(links)},
        update={"active": active_status},
    )
