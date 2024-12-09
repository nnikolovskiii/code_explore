from app.databases.mongo_db import MongoEntry

class GitUrl(MongoEntry):
    url: str
    active: bool

class CodeEmbeddingFlag(MongoEntry):
    url: str
    file_path: str

class CodeActiveFlag(MongoEntry):
    url: str
    file_path: str
    active: bool

class CodeContent(MongoEntry):
    url: str
    file_path: str
    content: str
    extension: str

class CodeChunk(MongoEntry):
    url: str
    file_path: str
    content_id: str
    content: str
    start_index: int
    end_index: int
    order: int
    code_len: int

class CodeContext(MongoEntry):
    url: str
    file_path: str
    chunk_id: str
    context: str

class Folder(MongoEntry):
    prev: str
    next: str
    is_folder: bool
    url: str
