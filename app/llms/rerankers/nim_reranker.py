import asyncio
import os
from typing import List

import aiohttp
from dotenv import load_dotenv

async def use_reranker(
        question: str,
        passages: List[str],
        top_k: int
):
    invoke_url = "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-3_2-nv-rerankqa-1b-v2/reranking"

    load_dotenv()
    nim_api_key = os.getenv("NIM_API_KEY")

    headers = {
        "Authorization": f"Bearer {nim_api_key}",
        "Accept": "application/json",
    }

    passage_dicts = [{"text": passage} for passage in passages]

    payload = {
        "model": "nvidia/llama-3.2-nv-rerankqa-1b-v2",
        "query": {
            "text": question
        },
        "passages": passage_dicts
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(invoke_url, headers=headers, json=payload) as response:
            response.raise_for_status()
            response_body = await response.json()
            rankings = [data["index"] for data in response_body["rankings"]]
            ranked_passages = [passages[rank] for rank in rankings[:top_k]]
            print(ranked_passages)
            return ranked_passages

async def test():
  await use_reranker(
    question="What is the GPU memory bandwidth of H100 SXM?",
    passages=[
      "The Hopper GPU is paired with the Grace CPU using NVIDIA's ultra-fast chip-to-chip interconnect, delivering 900GB/s of bandwidth, 7X faster than PCIe Gen5. This innovative design will deliver up to 30X higher aggregate system memory bandwidth to the GPU compared to today's fastest servers and up to 10X higher performance for applications running terabytes of data.",
      "A100 provides up to 20X higher performance over the prior generation and can be partitioned into seven GPU instances to dynamically adjust to shifting demands. The A100 80GB debuts the world's fastest memory bandwidth at over 2 terabytes per second (TB/s) to run the largest models and datasets.",
      "Accelerated servers with H100 deliver the compute power—along with 3 terabytes per second (TB/s) of memory bandwidth per GPU and scalability with NVLink and NVSwitch™."
    ],
    top_k=1
  )

asyncio.run(test())