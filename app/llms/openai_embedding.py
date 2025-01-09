import asyncio
import os
from dotenv import load_dotenv
import httpx
from typing import List


async def embedd_content_with_model(
        content: str
) -> List[float]:
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    url = 'https://api.openai.com/v1/embeddings'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }

    data = {
        'input': content,
        'model': 'text-embedding-3-large'
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        return response_data['data'][0]['embedding']
    else:
        response.raise_for_status()

# asyncio.run(embedd_content_with_model("Hello World"))