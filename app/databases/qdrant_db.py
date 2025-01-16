import asyncio
import uuid
from typing import List, Dict, Any, Optional, TypeVar, Callable, Awaitable, Tuple

from aiohttp import payload_type
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

    def __init__(self, url: Optional[str] = None):
        load_dotenv()
        url = os.getenv("QDRANT_URL") if url is None else url
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
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[float]:
        collection_name = entity.__class__.__name__ if collection_name is None else collection_name

        if not await self.collection_exists(collection_name):
            await self.create_collection(collection_name)

        vector = await embedd_content_with_model(value)
        payload = entity.model_dump()
        if metadata:
            payload.update(metadata)

        await self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    payload=payload,
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

    async def delete_records(self, collection_name: str, doc_filter: Dict[Tuple[str, str], Any]):
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
            print(f"Failed to delete records: {e}")

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
        filter: Optional[Dict[Tuple[str,str], Any]] = None,
        collection_name: Optional[str] = None,

    ) -> List[T]:
        collection_name = class_type.__name__ if collection_name is None else collection_name
        field_condition = QdrantDatabase._generate_filter(filters=filter)
        vector = await embedd_content_with_model(value)

        points =  await self.client.search(
            query_vector=vector,
            score_threshold=score_threshold,
            collection_name=collection_name,
            limit=top_k,
            query_filter=field_condition,
        )

        return [class_type(**point.payload) for point in points]

    async def transform_all(
            self,
            collection_name: str,
            function: Callable[[List[Record]], Awaitable[None]],
            with_vectors: bool = False,
            filter: Optional[Dict[Tuple[str,str], Any]] = None,
    ) -> List[Record]:
        field_condition = QdrantDatabase._generate_filter(filters=filter)
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
            if len(records) != 0:
                await function(records)
            else:
                print("MUSTAAAAAAAAAAAAAARD")
            offset = response[-1]
            if offset is None:
                break
        return records

    async def scroll(
            self,
            collection_name: str,
            with_vectors: bool = True,
            filter: Optional[Dict[Tuple[str, str], Any]] = None,
    ):
        field_condition = QdrantDatabase._generate_filter(filters=filter) if filter is not None else None
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
            yield records

            offset = response[-1]
            if offset is None:
                break

    async def get_first_record_by_filter(
            self,
            collection_name: str,
            filter: Optional[Dict[Tuple[str,str], Any]] = None,
    ) -> Record|None:
        filter_obj = QdrantDatabase._generate_filter(filters=filter)

        response = await self.client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_obj,
            limit=1
        )

        try:
            records = response[0]
            return records[0]
        except IndexError:
            print("There is no such record.")
            return None

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
        self, collection_name: str, filter: Optional[Dict[Tuple[str,str], Any]] = None
    ):
        field_condition = QdrantDatabase._generate_filter(filters=filter)
        await self.client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=field_condition,
            ),
        )

    async def update_points(
        self, collection_name: str, ids: List[str], update: Dict[str, Any]
    ):
        print(ids)
        print(update)
        await self.client.set_payload(
            collection_name=collection_name,
            wait=True,
            payload=update,
            points=ids,
        )

    @staticmethod
    def _generate_filter(filters: Optional[Dict[Tuple[str,str], Any]] = None):
        field_condition = None
        conditions = []
        for key_type, value in filters.items():
            condition = None
            key,type = key_type
            if type == "value":
                condition = models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                )
            elif type == "any":
                condition = models.FieldCondition(
                    key=key,
                    match=models.MatchAny(any=value),
                )
            conditions.append(condition)

        if filter:
            field_condition = models.Filter(
                must=conditions
            )
        return field_condition

