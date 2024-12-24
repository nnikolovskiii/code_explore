# import os
#
# from huggingface_hub import InferenceClient
#
# hf_api_key = os.getenv("HF_API_KEY")
#
# client = InferenceClient(api_key=hf_api_key)
#
# messages = [
# 	{
# 		"role": "user",
# 		"content": "What is the capital of France?"
# 	}
# ]
#
# completion = client.chat.completions.create(
#     model="meta-llama/Llama-3.2-3B-Instruct",
# 	messages=messages,
# 	max_tokens=500
# )
#
#
# print(completion.choices[0].message)
import asyncio

from app.databases.singletons import get_mongo_db, get_qdrant_db
from app.models.docs import DocsContent, DocsChunk, Link


async def lol():
	mdb = await get_mongo_db()
	chunks = await mdb.get_entries(DocsChunk,doc_filter={"active": True, "base_url": "https://fastapi.tiangolo.com"})
	for chunk in chunks:
		print(chunk)
	links = await mdb.get_entries(Link,doc_filter={"active": True, "base_url": "https://fastapi.tiangolo.com"})
	for link in links:
		print(link)


# asyncio.run(lol())
