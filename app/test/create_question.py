from app.llms.chat.json_response import get_json_response


def create_question_template(
        chunk: str,
        context: str = None
) -> str:
    response = ""
    if context is not None:
        response += f"""<document> 
{context}
</document> 
Here is the chunk that is extracted from the document above.
<chunk> 
{chunk} 
</chunk>
"""
    else:
        response += f"""<chunk>
{chunk}
</chunk>
"""

    response += """Create a question out of the context of the chunk. Ask the question like you are a user and try to get information from the documentation.
    
    Return the question in JSON format with key 'question'."""
    return response


async def create_question(
        chunk: str,
        context: str = None,
) -> str:
    template = create_question_template(chunk, context)
    response = await get_json_response(template=template, list_name="question",
                                       system_message="You are an AI assistant helping with writing questions for a documentation.")
    if "question" not in response:
        raise Exception("No question found")
    return response["question"]
