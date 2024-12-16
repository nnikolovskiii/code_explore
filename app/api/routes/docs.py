from typing import Annotated, List

from fastapi import HTTPException, APIRouter, Depends
from pydantic import BaseModel

from app.databases.mongo_db import MongoDBDatabase

import logging
import shutil

from app.databases.qdrant_db import QdrantDatabase
from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.docs_process.pre_process.extract_content import extract_contents
from app.docs_process.pre_process.traverse_sites import traverse_links, check_prev_links
from app.models.docs import DocsUrl, Link, DocsContent

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

mdb_dep = Annotated[MongoDBDatabase, Depends(get_mongo_db)]
qdb_dep = Annotated[QdrantDatabase, Depends(get_qdrant_db)]


@router.get("/extract_docs/")
async def extract_library(docs_url: str, override: bool, mdb: mdb_dep, qdb: qdb_dep):
    try:
        if override:
            pass
            await mdb.delete_entries(DocsContent, doc_filter={"base_url": docs_url})
            # await mdb.delete_entries(CodeChunk, doc_filter={"url": git_url})
            await mdb.delete_entries(DocsUrl, doc_filter={"url": docs_url})
            # await mdb.delete_entries(CodeContext, doc_filter={"url": git_url})
            await mdb.delete_entries(Link, doc_filter={"base_url": docs_url})
            # await qdb.delete_records(collection_name="CodeChunk", doc_filter={("url", "value"): git_url})
            # await mdb.delete_entries(CodeEmbeddingFlag, doc_filter={"url": git_url})
            # await mdb.delete_entries(CodeActiveFlag, doc_filter={"url": git_url})
            # await mdb.delete_entries(Folder, collection_name="TempFolder", doc_filter={"url": git_url})

        urls = await mdb.get_entries(DocsUrl, doc_filter={"url": docs_url})
        if len(urls) == 0:
            await mdb.add_entry(DocsUrl(url=docs_url, active=True))
            await traverse_links(docs_url, mdb)
            await extract_contents(docs_url, mdb)
            await check_prev_links(docs_url, mdb)
            return {"status": "success", "message": "Fetched links and processed successfully."}
        else:
            return {"status": "success", "message": "Links already fetched and processed."}
    except Exception as e:
        logging.exception("Error cloning library")
        raise HTTPException(status_code=500, detail=str(e))

#
# @router.post("/process_files/")
# async def process_files(file_dto: FileDto, git_url: str, mdb: mdb_dep, qdb: qdb_dep):
#     await process_code_files(
#         file_paths=file_dto.file_paths,
#         git_url=git_url,
#         mdb=mdb,
#         qdb=qdb,
#     )
#
# @router.post("/change_active_repos")
# async def change_active_repos(git_url_dto: GitUrlDto ,mdb: mdb_dep):
#     for git_url, active_status in zip(git_url_dto.git_urls, git_url_dto.active):
#         git_url_obj = await mdb.get_entry_from_col_value(
#             column_name="url",
#             column_value=git_url,
#             class_type=GitUrl
#         )
#         git_url_obj.active = active_status
#         await mdb.update_entry(git_url_obj)
#
# @router.post("/change_active_files/")
# async def _change_active_files(file_dto: FileActiveListDto, git_url:str, mdb: mdb_dep, qdb: qdb_dep):
#     await change_active_files(file_dto, git_url, mdb, qdb)
