from typing import Annotated, List

from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel

from app.databases.mongo_db import MongoDBDatabase

import logging
import shutil

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.docs_process.pre_process.extract_content import extract_contents
from app.docs_process.pre_process.traverse_sites import traverse_links, check_prev_links, set_parent_flags
from app.models.docs import DocsUrl, Link, DocsContent, DocsChunk, DocsContext, DocsEmbeddingFlag
from app.models.process import Process
from app.models.simple_process import create_simple_process, finish_simple_process, SimpleProcess

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
        selector: str,
        mdb: mdb_dep,
        qdb: qdb_dep,
        pattern_dto: PatternDto = None,
        selector_attrs: str = None
):
    try:
        docs_url = docs_url[:-1] if docs_url.endswith("/") else docs_url
        if override:
            pass
            await mdb.delete_entries(DocsContent, doc_filter={"base_url": docs_url})
            await mdb.delete_entries(DocsChunk, doc_filter={"base_url": docs_url})
            await mdb.delete_entries(DocsUrl, doc_filter={"url": docs_url})
            await mdb.delete_entries(DocsContext, doc_filter={"base_url": docs_url})
            await mdb.delete_entries(Link, doc_filter={"base_url": docs_url})
            await qdb.delete_records(collection_name="DocsChunk", doc_filter={("base_url", "value"): docs_url})
            await mdb.delete_entries(DocsEmbeddingFlag, doc_filter={"base_url": docs_url})
            await mdb.delete_entries(Process, doc_filter={"url": docs_url})
            await mdb.delete_entries(SimpleProcess, doc_filter={"url": docs_url})
            await mdb.delete_entries(Link, collection_name="TempLink", doc_filter={"base_url": docs_url})

        urls = await mdb.get_entries(DocsUrl, doc_filter={"url": docs_url})
        if len(urls) == 0:
            await mdb.add_entry(DocsUrl(url=docs_url, active=True))
            main_process = await create_simple_process(url=docs_url, mdb=mdb, process_type="main", type="docs", order=0)

            logging.info("traverse")
            process = await create_simple_process(url=docs_url, mdb=mdb, process_type="traverse", type="docs", order=1)
            await traverse_links(docs_url,pattern_dto.patterns, mdb)
            await finish_simple_process(process,mdb)

            logging.info("extract")
            process = await create_simple_process(url=docs_url, mdb=mdb, process_type="extract", type="docs", order=2)
            await extract_contents(docs_url,selector, selector_attrs, mdb)
            await finish_simple_process(process,mdb)

            logging.info("check")
            process = await create_simple_process(url=docs_url, mdb=mdb, process_type="check", type="docs", order=3)
            await check_prev_links(docs_url, mdb)
            await finish_simple_process(process,mdb)

            logging.info("parents")
            process = await create_simple_process(url=docs_url, mdb=mdb, process_type="parents", type="docs", order=4)
            await set_parent_flags(docs_url, mdb)
            await finish_simple_process(process,mdb)

            await finish_simple_process(main_process,mdb)

            return {"status": "success", "message": "Fetched links and processed successfully."}
        else:
            return {"status": "success", "message": "Links already fetched and processed."}
    except Exception as e:
        logging.exception("Error cloning library")
        raise HTTPException(status_code=500, detail=str(e))


