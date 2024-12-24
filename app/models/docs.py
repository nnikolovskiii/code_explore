from typing import Optional

from app.databases.mongo_db import MongoEntry

class DocsUrl(MongoEntry):
    url: str
    active: bool

class Link(MongoEntry):
    base_url: str
    prev_link: str
    link: str
    is_parent: bool = False
    active: bool = False
    color: Optional[str] = None
    processed: bool = False


class DocsContent(MongoEntry):
    base_url: str
    link: str
    content: str

class DocsChunk(MongoEntry):
    base_url: str
    link: str
    content_id: str
    content: str
    start_index: int
    end_index: int
    order: int
    doc_len: int
    active: bool = False
    processed: bool = False

class DocsEmbeddingFlag(MongoEntry):
    base_url: str
    link: str

class FinalDocumentChunk(MongoEntry):
    chunk_id: str
    content: str
    category: str
    link: str

class DocsContext(MongoEntry):
    base_url: str
    link: str
    chunk_id: str
    context: str

class Category(MongoEntry):
    chunk_id: str
    name: str