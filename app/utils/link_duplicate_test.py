import asyncio

from app.databases.mongo_db import MongoDBDatabase
from app.models.docs import Link


async def check_duplicate_links():
	mdb = MongoDBDatabase()
	links = await mdb.get_entries(Link, doc_filter={"base_url": 'https://docs.expo.dev'})
	links_set = set()
	for link in links:
		links_set.add(link.link)

	print(len(links_set), len(links))

asyncio.run(check_duplicate_links())