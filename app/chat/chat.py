from typing import List, Dict

from app.api.pipelines.generate_retrieval_docs_pipeline import GenerateRetrievalDocsPipeline
from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_qdrant_db
from app.llms.stream_chat.generic_stream_chat import generic_stream_chat
from app.models.docs import DocsChunk, DocsUrl



async def retrieve_relevant_chunks(
        question: str,
        mdb: MongoDBDatabase,
) -> List[DocsChunk]:
    qdb = await get_qdrant_db()
    docs_objs = await mdb.get_entries(DocsUrl, doc_filter={"active": True})
    docs_urls = [docs_obj.url for docs_obj in docs_objs]
    return await qdb.retrieve_similar_entries(
        value=question,
        class_type=DocsChunk,
        score_threshold=0.3,
        top_k=10,
        filter={("active", "value"): True, ("base_url", "any") : docs_urls}
    )


async def chat(
        message: str,
        system_message: str,
        mdb: MongoDBDatabase,
        history: List[Dict[str, str]] = None,
):
    relevant_chunks = await retrieve_relevant_chunks(message, mdb=mdb)
    references = {(relevant_chunk.link, relevant_chunk.link.split(relevant_chunk.base_url)[1]) for relevant_chunk in relevant_chunks}
    chunk_contents = [chunk.content for chunk in relevant_chunks]
    pipeline = GenerateRetrievalDocsPipeline(mdb=mdb)
    async for data in pipeline.stream_execute(
            instruction=message,
            chunks=chunk_contents,
            system_message=system_message,
            history=history,
    ):
        yield data

    yield "<div class='references'><p class='reference_header'>Sources:</p><div class='references_list'>"
    for reference, reference_name in references:
        yield f"""<div class="reference">
                        <a href="{reference}" target="_blank">
                            {reference_name}
                        </a>
                      </div>"""
    yield "</div></div>"
