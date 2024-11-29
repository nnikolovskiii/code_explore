from app.databases.mongo.db import MongoEntry


class GitUrl(MongoEntry):
    url: str
    path: str
    last_commit: str

