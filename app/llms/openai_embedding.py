import os
from dotenv import load_dotenv
import requests
import json
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

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        return response_data['data'][0]['embedding']
    else:
        response.raise_for_status()
