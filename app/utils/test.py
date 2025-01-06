import asyncio

from app.databases.mongo_db import MongoEntry
from app.databases.singletons import get_mongo_db

class Test(MongoEntry):
    name: str
    name1: str = "null"

async def test():
    mdb = await get_mongo_db()
    await mdb.delete_entries(Test)
    for i in range(3):
        test = Test(name=f"test{i}")
        await mdb.add_entry(test)
    i = 0
    await mdb.add_entry(Test(name=f"lolzi", name1="lol"))
    li = await mdb.get_entry_from_col_values(columns={"name": "lolzi", "name1": "lol"}, class_type=Test)
    print(li)

asyncio.run(test())
