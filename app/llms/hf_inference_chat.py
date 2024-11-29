import os
from typing import List, Dict

from huggingface_hub import InferenceClient
from dotenv import load_dotenv


async def chat_with_hf_inference(
        message: str,
        system_message: str,
        history: List[Dict[str, str]] = None,
        stream: bool = False,
):
    load_dotenv()
    hf_api_key = os.getenv("HF_API_KEY")
    hf_model = os.getenv("HF_MODEL")

    client = InferenceClient(model=hf_model, api_key=hf_api_key, headers={"x-use-cache":"false"})

    messages = get_messages_template(message, system_message, history)

    args = {
        "max_tokens": 15000,
        "messages": messages,
        "temperature": 0.5,
        "top_p": 0.8,
    }

    if stream:
        args["stream"] = True
        for stream_output in client.chat_completion(**args):
            yield stream_output["choices"][0]["delta"]["content"]

    else:
        args["stream"] = False
        output = client.chat_completion(**args)
        yield output.choices[0]["message"]["content"]


def get_messages_template(
        message: str,
        system_message: str,
        history: List[Dict[str, str]] = None,
):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": message},
    ] if history is None else [{"role": "user", "content": message}]

    all_messages = [] if history is None else history
    all_messages.extend(messages)
    print(all_messages)
    return all_messages

