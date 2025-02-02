import logging
from typing import Type, Any, Dict

from bson import ObjectId

from app.container import container
from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from app.databases.qdrant_db import QdrantDatabase
from app.docs_process.group_process import GroupProcess, T
from app.llms.models import EmbeddingModel

from app.models.docs import DocsChunk, DocsContext, Link

logger = logging.getLogger(__name__)


class EmbeddChunk(MongoEntry):
    chunk_id: str
    url: str
    link: str


class EmbeddingProcess(GroupProcess):
    qdb: QdrantDatabase

    def __init__(self, mdb: MongoDBDatabase, class_type: Type[T], group_id: str, qdb: QdrantDatabase):
        super().__init__(mdb,group_id, class_type)
        self.qdb = qdb

    @property
    def execute_process_filters(self) -> Dict[str, Any]:
        return {"url": self.group_id}

    @property
    def process_type(self) -> str:
        return "post"

    @property
    def stream_filters(self) -> Dict[str, Any]:
        return {"processed": False, "active": True}

    @property
    def process_name(self) -> str:
        return "embedd"

    async def pre_execute_process(self):
        chat_service = container.chat_service()
        embedding_model = await chat_service.get_model("text-embedding-3-large", EmbeddingModel)
        await self.qdb.set_embedding_model(embedding_model)

    async def post_execute_process(self):
        await self._set_embedding_flags(self.group_id)

    async def execute_single(self, chunk: EmbeddChunk):
        chunk = await self.mdb.get_entry(ObjectId(chunk.chunk_id), DocsChunk)

        context = await self.mdb.get_entry_from_col_value(
            column_name="chunk_id",
            column_value=chunk.id,
            class_type=DocsContext
        )
        if context is not None:
            chunk.content = context.context + chunk.content

        try:
            await self.qdb.embedd_and_upsert_record(
                value=chunk.content,
                entity=chunk,
                metadata={"active": True}
            )

            chunk.processed = True
            await self.mdb.update_entry(chunk)

        except Exception as e:
            logging.error(e)


    async def add_not_processed(self, link_obj: Link) -> int:
            count = 0
            chunks = await self.mdb.get_entries(DocsChunk, doc_filter={"link": link_obj.link})
            for chunk in chunks:
                if not chunk.processed:
                    await self.mdb.add_entry(EmbeddChunk(chunk_id=chunk.id, url=self.group_id, link=chunk.link))
                    count += 1

            return count

    async def _set_embedding_flags(
            self,
            docs_url: str,
    ):
        async for link_obj in self.mdb.stream_entries(
                class_type=Link,
                doc_filter={"base_url": docs_url, "processed": False, "active": True},
        ):
            num_processed_chunks = await self.mdb.count_entries(DocsChunk,
                                                           doc_filter={"link": link_obj.link, "base_url": docs_url,
                                                                       "processed": True})
            first_chunk = await self.mdb.get_entry_from_col_value(
                column_name="link",
                column_value=link_obj.link,
                class_type=DocsChunk
            )

            if first_chunk and first_chunk.doc_len == num_processed_chunks:
                link_obj.processed = True
                await self.mdb.update_entry(link_obj)
            elif num_processed_chunks == 0:
                link_obj.processed = True
                await self.mdb.update_entry(link_obj)

