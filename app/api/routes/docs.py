from typing import Annotated, List

from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel

from app.databases.mongo_db import MongoDBDatabase

import logging

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.docs_process.pre_process.check_parent_link import CheckParentLinkProcess
from app.docs_process.pre_process.extract_content import ExtractContentProcess
from app.docs_process.pre_process.set_parent_flags import SetParentFlags
from app.docs_process.pre_process.traverse_sites import TraverseSitesProcess, TraverseSitesBatch
from app.models.docs import DocsUrl, Link, DocsContent, DocsChunk, DocsContext, DocsEmbeddingFlag
from app.models.process_tracker import ProcessTracker, create_process, finish_process

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


class PatternDto(BaseModel):
    patterns: List[str]


@router.post("/extract_docs/")
async def extract_library(
        docs_url: str,
        override: bool,
        selector_type: str,
        selector: str,
        mdb: mdb_dep,
        qdb: qdb_dep,
        pattern_dto: PatternDto = None,
        selector_attrs: str = None
):
    try:
        docs_url = docs_url[:-1] if docs_url.endswith("/") else docs_url
        await mdb.delete_entries(DocsContent, doc_filter={"base_url": docs_url})
        await mdb.delete_entries(DocsChunk, doc_filter={"base_url": docs_url})
        await mdb.delete_entries(DocsUrl, doc_filter={"url": docs_url})
        await mdb.delete_entries(DocsContext, doc_filter={"base_url": docs_url})
        if True:
            await mdb.delete_entries(Link, doc_filter={"base_url": docs_url})
            await mdb.delete_entries(TraverseSitesBatch, doc_filter={"docs_url": docs_url})
        await qdb.delete_records(collection_name="DocsChunk", doc_filter={("base_url", "value"): docs_url})
        await mdb.delete_entries(DocsEmbeddingFlag, doc_filter={"base_url": docs_url})
        await mdb.delete_entries(ProcessTracker, doc_filter={"url": docs_url})

        await mdb.add_entry(DocsUrl(url=docs_url, active=True))
        main_process = await create_process(url=docs_url, mdb=mdb, process_type="main", type="docs", order=0,
                                            group="pre")

        logging.info("traverse")
        traverse_process = TraverseSitesProcess(mdb=mdb, group_id=docs_url, patterns=pattern_dto.patterns, order=1)
        await traverse_process.execute_process()

        logging.info("extract")
        extract_process = ExtractContentProcess(
            mdb=mdb,
            order=2,
            group_id=docs_url,
            selector=selector,
            selector_type=selector_type,
            selector_attrs=selector_attrs
        )
        await extract_process.execute_process()

        logging.info("check")
        check_parent_process = CheckParentLinkProcess(mdb=mdb, group_id=docs_url, order=3)
        await check_parent_process.execute_process()

        logging.info("parents")
        parents_process = SetParentFlags(mdb=mdb, group_id=docs_url, order=4)
        await parents_process.execute_process()

        await finish_process(main_process, mdb)
        return {"status": "success", "message": "Fetched links and processed successfully."}
    except Exception as e:
        logging.exception("Error cloning library")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_docs_urls/")
async def get_git_urls(mdb: mdb_dep):
    try:
        docs_urls = await mdb.get_entries(DocsUrl)
        return {"docs_urls": docs_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activate_docs_url/")
async def activate_docs_url(docs_url: str, active_status: bool, mdb: mdb_dep):
    docs_url_obj = await mdb.get_entry_from_col_value(
        column_name="url",
        column_value=docs_url,
        class_type=DocsUrl
    )
    docs_url_obj.active = active_status
    await mdb.update_entry(docs_url_obj)
