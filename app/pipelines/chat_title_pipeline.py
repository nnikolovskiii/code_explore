from app.models.pipeline import ChatPipeline


class ChatTitlePipeline(ChatPipeline):
    @property
    def response_type(self) -> str:
        return "dict"

    def template(self, message: str) -> str:
        return f"""Given the below user question your job is to create a name/title for the whole chat. Write the title with maximum 3 words. Make it encompass the key concepts of the question.
Question: {message}

Return in json format: {{"title": "..."}}"""
