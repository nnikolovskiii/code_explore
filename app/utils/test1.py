import os

from huggingface_hub import InferenceClient

hf_api_key = os.getenv("HF_API_KEY")

client = InferenceClient(api_key=hf_api_key)

messages = [
	{
		"role": "user",
		"content": "What is the capital of France?"
	}
]

completion = client.chat.completions.create(
    model="meta-llama/Llama-3.2-3B-Instruct",
	messages=messages,
	max_tokens=500
)


print(completion.choices[0].message)