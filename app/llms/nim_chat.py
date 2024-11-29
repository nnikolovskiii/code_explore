import os
from dotenv import load_dotenv
from openai import OpenAI


def chat_with_nim(
        message: str,
        system_message:str
) -> str:
    load_dotenv()
    nim_url = os.getenv("NIM_URL")
    nim_api_key = os.getenv("NIM_API_KEY")
    nim_model = os.getenv("NIM_MODEL")

    client = OpenAI(
        base_url=nim_url,
        api_key=nim_api_key
    )

    completion = client.chat.completions.create(
        model=nim_model,
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": message
            }
        ],
        temperature=0.7,
        top_p=0.8,
        max_tokens=3000
    )

    if completion.choices[0].message.content is not None:
        return completion.choices[0].message.content.strip()
    else:
        raise Exception("No content returned from completion.")
