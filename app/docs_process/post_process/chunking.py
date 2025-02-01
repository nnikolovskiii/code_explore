import logging
from typing import Type, Optional

from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from langchain_text_splitters import Language

from app.docs_process.process import Process, T
from app.models.docs import DocsChunk, DocsContent, Link
from app.models.splitters.text_splitters import TextSplitter


class ChunkLink(MongoEntry):
    link: str
    url: str


class ChunkProcess(Process):
    text_splitter: TextSplitter

    def __init__(self, mdb: MongoDBDatabase, class_type: Type[T], group_id: str,
                 text_splitter: Optional[TextSplitter] = None):
        super().__init__(mdb, class_type, group_id)
        self.text_splitter = text_splitter if text_splitter is not None else (
            TextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                length_function=len,
            ))

        separators = self.text_splitter.get_separators_for_language(Language.MARKDOWN)
        self.text_splitter._separators = separators

    @property
    def process_type(self) -> str:
        return "chunk"

    async def execute_single(self, chunk_link: ChunkLink):
        content = await self.mdb.get_entry_from_col_value(
            column_name="link",
            column_value=chunk_link.link,
            class_type=DocsContent
        )
        try:
            await self._chunk_content(content, self.text_splitter, True)
        except Exception as e:
            logging.error(e)

    async def add_not_processed(self, link_obj: Link) -> int:
        count = 0
        exist_one_chunk = await self.mdb.get_entry_from_col_value(
            column_name="link",
            column_value=link_obj.link,
            class_type=DocsChunk
        )
        if exist_one_chunk is None:
            await self.mdb.add_entry(ChunkLink(link=link_obj.link, url=self.group_id))
            count += 1

        return count

    async def _chunk_content(
            self,
            content: DocsContent,
            text_splitter: TextSplitter,
            huge_content: bool = False
    ):
        texts = text_splitter.split_text(content.content)

        if huge_content or (len(texts) < 50 and not huge_content):
            for i, text in enumerate(texts):
                doc_chunk = DocsChunk(
                    base_url=content.base_url,
                    link=content.link,
                    content_id=content.id,
                    content=text[0],
                    start_index=int(text[1][0]),
                    end_index=int(text[1][1]),
                    order=i,
                    doc_len=len(texts)
                )
                await self.mdb.add_entry(doc_chunk)
