import requests
import json


def chat_with_custom_api(
        message: str
) -> str:
    url = 'https://b8b2-34-143-191-121.ngrok-free.app/generate_text/'

    headers = {
        'Content-Type': 'application/json',
    }

    data = {
        'prompt': message
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        return response_data['generated_text']
    else:
        response.raise_for_status()