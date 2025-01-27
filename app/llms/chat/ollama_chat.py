import requests
import json

def chat_with_ollama(
        message: str,
        system_message: str,
) -> str:
    url = 'http://localhost:11434/api/chat'

    data = {
        'model': 'phi3.5:3.8b-mini-instruct-q8_0',
        'messages': [
            {
                "role": "system",
                "content": system_message,
            },
            {
              "role": "user",
              "content": message
            }
        ],
        'stream': False
    }

    response = requests.post(url, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        return response_data['message']['content']
    else:
        response.raise_for_status()
