import asyncio
import uuid
from typing import List, Dict, Any, Optional, TypeVar, Callable, Awaitable
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client import models
from typing import Type as TypingType

from app.llms.openai_embedding import embedd_content_with_model
from pydantic import BaseModel
from qdrant_client.conversions import common_types as types
from dotenv import load_dotenv
import os
from qdrant_client.http.models import Record

class SearchOutput(BaseModel):
    score: float
    value_type: str


T = TypeVar("T")


class QdrantDatabase:
    client: AsyncQdrantClient

    def __init__(self):
        load_dotenv()
        url = os.getenv("URL")
        self.client = AsyncQdrantClient(url=f"http://{url}:6333")

    async def collection_exists(self, collection_name: str) -> bool:
        return await self.client.collection_exists(collection_name)

    async def create_collection(self, collection_name: str):
        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=3072, distance=models.Distance.COSINE),
        )

    async def embedd_and_upsert_record(
        self,
        value: str,
        entity: T,
        collection_name: Optional[str] = None,
    ) -> List[float]:
        collection_name = entity.__class__.__name__ if collection_name is None else collection_name

        if not await self.collection_exists(collection_name):
            await self.create_collection(collection_name)

        vector = await embedd_content_with_model(value)

        await self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    payload=entity.model_dump(),
                    vector=vector,
                ),
            ],
        )

        return vector

    async def delete_all_collections(self):
        collections = await self.client.get_collections()
        for collection in collections.collections:
            await self.client.delete_collection(collection_name=collection.name)

    async def delete_collection(self, collection_name: str):
        await self.client.delete_collection(collection_name=collection_name)

    async def delete_records(self, collection_name: str, doc_filter: Dict[str, Any]):
        if not doc_filter:
            raise ValueError("Filter cannot be empty to prevent accidental deletion of all records.")


        filter_obj = QdrantDatabase._generate_filter(doc_filter)
        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=filter_obj
                )
            )
        except Exception as e:
            raise RuntimeError(f"Failed to delete records: {e}")

    async def retrieve_point(
        self, collection_name: str, point_id: str
    ) -> Record:
        points = await self.client.retrieve(
            collection_name=collection_name,
            ids=[point_id],
            with_vectors=True,
        )
        return points[0]

    async def retrieve_similar_entries(
        self,
        value: str,
        class_type: TypingType[T],
        score_threshold: float,
        top_k: int,
        filter: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None,

    ) -> List[T]:
        collection_name = class_type.__name__ if collection_name is None else collection_name
        field_condition = QdrantDatabase._generate_filter(filter=filter)
        vector = await embedd_content_with_model(value)

        points =  await self.client.search(
            query_vector=vector,
            score_threshold=score_threshold,
            collection_name=collection_name,
            limit=top_k,
            query_filter=field_condition,
        )

        return [class_type(**point.payload) for point in points]

    async def transform(
        self,
        collection_name: str,
        function: Callable[[List[Record]], Awaitable[None]],
        with_vectors: bool = False,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Record]:
        field_condition = QdrantDatabase._generate_filter(filter=filter)
        offset = None
        while True:
            response = await self.client.scroll(
                collection_name=collection_name,
                scroll_filter=field_condition,
                limit=50,
                offset=offset,
                with_payload=True,
                with_vectors=with_vectors,
            )
            records = response[0]
            await function(records)
            offset = response[-1]
            if offset is None:
                break
        return records

    async def upsert_record(
        self,
        unique_id: str,
        collection_name: str,
        payload: Dict[str, Any],
        vector: List[float],
    ) -> None:
        if not await self.collection_exists(collection_name):
            await self.create_collection(collection_name)

        await self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=unique_id,
                    payload=payload,
                    vector=vector,
                ),
            ]
        )

    async def delete_points(
        self, collection_name: str, filter: Optional[Dict[str, Any]] = None
    ):
        field_condition = QdrantDatabase._generate_filter(filter=filter)
        await self.client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=field_condition,
            ),
        )

    async def update_points(
        self, collection_name: str, ids: List[str], update: Dict[str, Any]
    ):
        await self.client.set_payload(
            collection_name=collection_name,
            wait=True,
            payload=update,
            points=ids,
        )

    @staticmethod
    def _generate_filter(filter: Optional[Dict[str, Any]] = None):
        field_condition = None
        if filter:
            field_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                    for key, value in filter.items()
                ]
            )
        return field_condition


async def update_active_status_fn(
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


async def update_active_status(
        collection_name: str,
        filter: Optional[Dict[str, Any]] = None,
        update: Dict[str, Any] = None,
):
    if update is None:
        raise ValueError("Update payload cannot be None.")

    qdb = QdrantDatabase()

    async def process_records(records: List[Record]):
        await update_active_status_fn(records, qdb, collection_name, update)

    await qdb.transform(
        collection_name=collection_name,
        function=process_records,
        filter=filter,
    )

asyncio.run(update_active_status(
    collection_name="CodeChunk",
    filter={"id":"6755a2a51849b1cb4e7513a6"},
    update={"url":"lol"}
))
