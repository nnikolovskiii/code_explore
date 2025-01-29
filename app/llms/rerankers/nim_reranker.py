from typing import List, Tuple

import aiohttp

from app.llms.models import Reranker


class NimReranker(Reranker):
    async def generate(self, query: str, documents: List[str], threshold: float, top_k: int) -> List[Tuple[str, float]]:
        invoke_url = f"https://ai.api.nvidia.com/v1/retrieval/{self.chat_model_config.name}/reranking"

        headers = {
            "Authorization": f"Bearer {self.chat_api.api_key}",
            "Accept": "application/json",
        }

        passage_dicts = [{"text": passage} for passage in documents]

        payload = {
            "model": self.chat_model_config.name,
            "query": {
                "text": query
            },
            "passages": passage_dicts
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(invoke_url, headers=headers, json=payload) as response:
                response.raise_for_status()
                response_body = await response.json()
                rankings = [data["index"] for data in response_body["rankings"]]
                ranked_passages = [documents[rank] for rank in rankings[:top_k]]
                return [(doc, 1.0) for doc in ranked_passages]
