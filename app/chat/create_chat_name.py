from app.llms.json_response import get_json_response


def create_chat_name_template(
        message: str,
):
    return f"""Given the below user question your job is to create a name/title for the whole chat. Write the title with maximum 3 words. Make it encompass the key concepts of the question.

Question: {message}

Return in json format: {{"title": "..."}}
"""


async def create_chat_name(
        message: str,
) -> str:
    template = create_chat_name_template(message=message)
    response = await get_json_response(
        template,
        system_message="You are an AI assistant designed in providing contextual summaries of code."
    )
    if "title" in response:
        return response["title"]
    else:
        raise KeyError("Key 'title' not found in the response.")
