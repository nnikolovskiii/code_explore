import os
from typing import List, Tuple

import cohere
import asyncio

from dotenv import load_dotenv

from app.llms.models import Reranker


class CohereReranker(Reranker):
    async def generate(
            self,
            query: str,
            documents: List[str],
            threshold: float,
            top_k: int
    ) -> List[Tuple[str, float]]:
        co = cohere.AsyncClient(api_key=self.chat_api.api_key)

        response = await co.rerank(
            model=self.chat_model_config.name,
            query=query,
            documents=documents,
            top_n=top_k
        )

        index_scores = [(elem.index, elem.relevance_score) for elem in response.results]
        docs_scores = []
        for index, score in index_scores:
            if score > threshold:
                docs_scores.append((documents[index], score))

        return docs_scores
