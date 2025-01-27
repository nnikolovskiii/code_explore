from app.llms.chat.json_response import get_json_response


def check_quality_template(
        chunk: str
) -> str:
    return f"""Text:
{chunk}

Above is a given text. You job is to determine the quality of the text for generating questions. 
If the text has quality, rich or precise information then return yes.
If the text has reference, navigational or not-concrete information than return no.

Return in json with key 'verdict'"""

async def check_quality(chunk: str) -> str:
    template = check_quality_template(chunk)
    response = await get_json_response(
        template=template,
        list_name="verdict",
        system_message="You are a helpful AI assistant that analyzes content.",
        chat_model="hf_inf"
    )
    return response["verdict"]