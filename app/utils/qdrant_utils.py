from typing import Optional, Dict, Any, List, Tuple

from qdrant_client.conversions.common_types import Record

from app.databases.qdrant_db import QdrantDatabase


async def update_records_fn(
        records: List[Record],
        qdb: QdrantDatabase,
        collection_name: str,
        update: Dict[str, Any],
):
    ids = [record.id for record in records]
    await qdb.update_points(
        collection_name=collection_name,
        ids=ids,
        update=update,
    )


async def update_records(
        qdb: QdrantDatabase,
        collection_name: str,
        filter: Optional[Dict[Tuple[str, str], Any]] = None,
        update: Dict[str, Any] = None,
):
    if update is None:
        raise ValueError("Update payload cannot be None.")

    async def process_records(records: List[Record]):
        await update_records_fn(records, qdb, collection_name, update)

    await qdb.transform_all(
        collection_name=collection_name,
        function=process_records,
        filter=filter,
    )

async def _print_records(
        qdb: QdrantDatabase,
        collection_name: str,
        filter: Optional[Dict[Tuple[str, str], Any]] = None,
):
    async def print_records(records: List[Record]):
        print(len(records))

    await qdb.transform_all(
        collection_name=collection_name,
        function=print_records,
        filter=filter,
    )

async def _test_print_records():
    qdb = QdrantDatabase()
    for link in ["https://fastapi.tiangolo.com/python-types", "https://fastapi.tiangolo.com/advanced/response-headers", "https://fastapi.tiangolo.com/tutorial/extra-data-types"]:
        await _print_records(qdb, "DocsChunk", filter={("link", "value"): link, ("active", "value"): True},
)

# asyncio.run(_test_print_records())
