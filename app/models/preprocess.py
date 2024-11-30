from bson import ObjectId

from app.databases.mongo.db import MongoEntry

class Content(MongoEntry):
    link: str
    content: str

class DocumentChunk(MongoEntry):
    content_id: str
    content: str
    start_index: int
    end_index: int
    order: int

class Context(MongoEntry):
    chunk_id: str
    context: str

class Category(MongoEntry):
    chunk_id: str
    name: str