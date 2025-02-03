from typing import List, Dict

from app.container import container
from app.llms.models import StreamChatLLM, Reranker
from app.pipelines.generate_retrieval_docs_pipeline import GenerateRetrievalDocsPipeline
from app.databases.mongo_db import MongoDBDatabase
from app.databases.singletons import get_qdrant_db
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
        score_threshold=0.0,
        top_k=100,
        filter={("active", "value"): True, ("base_url", "any") : docs_urls}
    )

async def rerank_chunks(
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
        active_model: StreamChatLLM,
        history: List[Dict[str, str]] = None,
):
    chat_service = container.chat_service()
    retrieved_chunks = await retrieve_relevant_chunks(message, mdb=mdb)
    print("MUSTARD")
    print(len(retrieved_chunks))

    reranker = await chat_service.get_model("rerank-v3.5", Reranker)
    index_scores = await reranker.generate(message, [chunk.content for chunk in retrieved_chunks], threshold=0.0, top_k=10)

    relevant_chunks = [retrieved_chunks[index] for index, _ in index_scores]
    print(len(relevant_chunks))
    references = {(relevant_chunk.link, relevant_chunk.link.split(relevant_chunk.base_url)[1]) for relevant_chunk in relevant_chunks}

    chunk_contents = [chunk.content for chunk in relevant_chunks]
    pipeline = GenerateRetrievalDocsPipeline(stream_chat_llm=active_model, mdb=mdb)
    async for data in pipeline.execute(
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
