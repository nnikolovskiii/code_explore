from app.databases.mongo_db import MongoEntry

class Content(MongoEntry):
    link: str
    content: str

class DocumentChunk(MongoEntry):
    content_id: str
    content: str
    start_index: int
    end_index: int
    order: int

class FinalDocumentChunk(MongoEntry):
    chunk_id: str
    content: str
    category: str
    link: str

class Context(MongoEntry):
    chunk_id: str
    context: str

class Category(MongoEntry):
    chunk_id: str
    name: str