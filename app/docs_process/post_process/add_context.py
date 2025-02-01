import logging
from typing import Type

from bson import ObjectId

from app.container import container
from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from app.docs_process.process import Process, T
from app.llms.models import ChatLLM
from app.models.docs import DocsChunk, Link, DocsContent, DocsContext
from app.pipelines.chunk_context_pipeline import ChunkContextPipeline


class AddContextChunk(MongoEntry):
    chunk_id: str
    link: str
    url: str


class AddContextProcess(Process):
    context_len: int

    def __init__(self, mdb: MongoDBDatabase, class_type: Type[T], group_id: str, context_len: int = 50000):
        super().__init__(mdb, class_type, group_id)
        self.context_len = context_len

    @property
    def process_type(self) -> str:
        return "context"

    async def execute_single(self, context_chunk: AddContextChunk):
        chunk = await self.mdb.get_entry(ObjectId(context_chunk.chunk_id), DocsChunk)

        while True:
            try:
                await self._add_context(chunk, self.context_len)
                chunk.context_processed = True
                await self.mdb.update_entry(chunk)
                break
            except Exception as e:
                logging.info(f"Adjusting the context_length. Current context length: {self.context_len}")
                self.context_len -= 500
                logging.error(e)

            if self.context_len < 1000:
                self.context_len = 50000
                break

    async def add_not_processed(self, link_obj: Link) -> int:
        count = 0
        chunks = await self.mdb.get_entries(DocsChunk, doc_filter={"link": link_obj.link})
        chunks = [chunk for chunk in chunks if chunk.doc_len != 1]
        for chunk in chunks:
            if not chunk.context_processed:
                await self.mdb.add_entry(AddContextChunk(chunk_id=chunk.id, url=self.group_id, link=chunk.link))
                count += 1

        return count

    async def _add_context(
            self,
            chunk: DocsChunk,
            context_len: int
    ):
        chat_service = container.chat_service()
        if chunk.doc_len > 1:
            context = await self._get_surrounding_context(chunk=chunk, context_len=context_len)

            chat_llm = await chat_service.get_model("Qwen/Qwen2.5-Coder-32B-Instruct", class_type=ChatLLM)
            pipeline = ChunkContextPipeline(chat_llm=chat_llm)
            response = await pipeline.execute(context=context, chunk_text=chunk.content)
            await self.mdb.add_entry(DocsContext(
                base_url=chunk.base_url,
                link=chunk.link,
                chunk_id=chunk.id,
                context=response,
            ))

    async def _get_surrounding_context(
            self,
            chunk: DocsChunk,
            context_len: int
    ) -> str:
        start_index = chunk.start_index
        end_index = chunk.end_index

        content_obj = await self.mdb.get_entry(ObjectId(chunk.content_id), DocsContent)
        content = content_obj.content

        tmp1 = min(end_index + context_len, len(content))
        tmp2 = max(start_index - context_len, 0)

        if tmp2 == 0:
            tmp1 = min(end_index + context_len + (context_len - start_index), len(content))

        if tmp1 == len(content):
            tmp2 = max(start_index - context_len - (context_len - (len(content) - end_index)), 0)

        after_context = content[end_index:tmp1] + "..."
        before_context = "..." + content[tmp2:start_index]

        return before_context + chunk.content + after_context
