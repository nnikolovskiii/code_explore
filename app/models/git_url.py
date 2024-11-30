from app.databases.mongo_db import MongoEntry


class GitUrl(MongoEntry):
    url: str
    path: str
    last_commit: str

