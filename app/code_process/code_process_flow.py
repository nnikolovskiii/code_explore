from typing import List

from pydantic import BaseModel

from app.code_process.post_process.active_status import update_records
from app.code_process.post_process.add_context import add_context_chunks
from app.code_process.post_process.embedd_chunks import create_final_chunks, embedd_chunks
from app.code_process.pre_process.extract_content import chunk_files
from app.databases.mongo_db import MongoDBDatabase
from app.databases.qdrant_db import QdrantDatabase
from app.models.code import Folder

class FileActiveListDto(BaseModel):
    file_paths: List[str]
    active: List[bool]


async def process_code_files(
        file_paths: List[str],
        git_url: str,
        mdb: MongoDBDatabase,
        qdb: QdrantDatabase,
):
    chunks = await chunk_files(file_paths=file_paths, git_url=git_url, mdb=mdb)
    contexts = await add_context_chunks(mdb=mdb, chunks=chunks)
    final_chunks = await create_final_chunks(mdb=mdb, chunks=chunks, contexts=contexts)
    await embedd_chunks(mdb=mdb, qdb=qdb, chunks=final_chunks)

async def change_active_files(file_dto: FileActiveListDto, git_url:str, mdb: MongoDBDatabase, qdb: QdrantDatabase):
    await process_code_files(
        file_paths=file_dto.file_paths,
        git_url=git_url,
        mdb=mdb,
        qdb=qdb,
    )

    for file_path, active_status in zip(file_dto.file_paths, file_dto.active):
        code_active_flag = await mdb.get_entry_from_col_value(
            column_name="next",
            column_value=file_path,
            class_type=Folder,
        )

        code_active_flag.active = active_status
        await mdb.update_entry(code_active_flag)

        record = await update_records(
            qdb=qdb,
            collection_name="CodeChunk",
            filter={("file_path","value"): file_path},
            update={"active": active_status},
        )
