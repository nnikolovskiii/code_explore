import asyncio
from typing import List

from bson import ObjectId
from tqdm import tqdm

from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_mongo_db
from app.llms.generic_chat import generic_chat
from app.llms.json_response import get_json_response
from app.models.code import CodeChunk, CodeContent, CodeContext, CodeEmbeddingFlag
from app.models.docs import Content, DocumentChunk, Context, Category, FinalDocumentChunk


def create_chat_name_template(
        message: str,
):
    return f"""Given the below user question your job is to create a name/title for the whole chat. Write the title with maximum 3 words. Make it encompass the key concepts of the question.

Question: {message}

Return in json format: {{"title": "..."}}
"""


async def create_chat_name(
        message: str,
) -> str:
    template = create_chat_name_template(message=message)
    response = await get_json_response(
        template,
        system_message="You are an AI assistant designed in providing contextual summaries of code."
    )
    if "title" in response:
        return response["title"]
    else:
        raise KeyError("Key 'title' not found in the response.")
