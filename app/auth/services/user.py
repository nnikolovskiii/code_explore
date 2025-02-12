from pydantic import EmailStr

from app.auth.models.user import User
from app.databases.mongo_db import MongoDBDatabase


class UserService:
    mdb: MongoDBDatabase

    def __init__(self, mdb: MongoDBDatabase):
        self.mdb = mdb

    async def check_user_exist(self, email: EmailStr) -> bool:
        existing_user = await self.mdb.get_entry_from_col_values(
            columns={"email": email},
            class_type=User
        )
        return existing_user is not None

    async def get_user(self, email: EmailStr) -> User|None:
        user = await self.mdb.get_entry_from_col_values(
            columns={"email": email},
            class_type=User
        )

        return user