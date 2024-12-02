from app.databases.mongo_db import MongoEntry


class GitUrl(MongoEntry):
    url: str
    path: str

class CodeContent(MongoEntry):
    file_path: str
    content: str
    extension: str

class CodeChunk(MongoEntry):
    content_id: str
    content: str
    start_index: int
    end_index: int
    order: int
    file_path: str
    code_len: int

class FinalCodeChunk(MongoEntry):
    chunk_id: str
    content: str
    file_path: str