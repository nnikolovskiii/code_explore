import asyncio

from app.models.pipeline import Pipeline


class ChatNamePipeline(Pipeline):
    def template(self, message: str) -> str:
        return f"""Given the below user question your job is to create a name/title for the whole chat. Write the title with maximum 3 words. Make it encompass the key concepts of the question.

        Question: {message}

        Return in json format: {{"title": "..."}}
        """


async def test():
    pipeline = ChatNamePipeline()
    response = await pipeline.execute_flow_dict(message="What do you think of the Milkiway Galaxy?")
    print(response)

asyncio.run(test())