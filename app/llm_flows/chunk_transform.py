from app.llm_flows.json_response import get_json_response
from app.llms.generic_chat import generic_chat


def summarize_chunk_template(chunk: str):
    return f"""You are given a text below. Your job is to briefly summarize the text. The text could be documentation, code or something else. Always write the summary with words and low to none code.

Text:
{chunk}

Return only the brief summary.
"""

def short_description_template(text: str):
    return f"""YOu are give a text below, which is some form of summary. Your job is to write a one sentence description of the text. Do not write more than one sentence.

Text:
{text}

Return the one sentence description in json with key "sentence".
"""

def summarize_chunk(chunk:str) -> str:
    template = summarize_chunk_template(chunk)
    response = generic_chat(template)
    return response

def short_description(text: str):
    template = short_description_template(text)
    json_data = get_json_response(template)
    return json_data["sentence"]