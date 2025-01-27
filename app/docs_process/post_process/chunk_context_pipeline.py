from app.models.pipeline import Pipeline


class ChunkContextPipeline(Pipeline):
    @property
    def response_type(self) -> str:
        return "str"

    def template(self, context: str, chunk_text:str) -> str:
        return f"""<document> 
{context}
</document> 
Here is the chunk we want to situate within the whole document which is part of a code documentation.
<chunk> 
{chunk_text} 
</chunk> 
Give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Make it a couple of sentences long.
"""