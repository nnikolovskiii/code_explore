from pydantic import EmailStr

from app.databases.mongo_db import MongoEntry


class User(MongoEntry):
    email: EmailStr
    hashed_password: str
    is_google_auth: bool = False
    full_name: str
