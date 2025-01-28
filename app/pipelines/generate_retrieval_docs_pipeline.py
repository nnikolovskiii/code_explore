from typing import List

from app.models.pipeline import StreamPipeline


class GenerateRetrievalDocsPipeline(StreamPipeline):
    @property
    def response_type(self) -> str:
        return "stream"

    def template(self, chunks: List[str], instruction: str) -> str:
        return f"""You are a task-execution agent. Execute the request exactly as specified.

# Available Context (Use only if directly relevant):
{"\n\n".join([f"Context Source {i + 1}\n{chunk}\n" for i, chunk in enumerate(chunks)]) if chunks else "No provided context. Proceed using general knowledge."}

# Task to Perform:
{instruction}

Response:"""
