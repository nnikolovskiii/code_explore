from app.databases.mongo_db import MongoEntry

class GitUrl(MongoEntry):
    url: str

class CodeContent(MongoEntry):
    url: str
    file_path: str
    content: str
    extension: str
    embedded: bool = False

class CodeChunk(MongoEntry):
    url: str
    content_id: str
    content: str
    start_index: int
    end_index: int
    order: int
    code_len: int

class FinalCodeChunk(MongoEntry):
    url: str
    file_path: str
    content: str
    order: int
    code_len: int

class Folder(MongoEntry):
    prev: str
    next: str
    is_folder: bool
    git_url: str
    embedded: bool = False
