from __future__ import annotations

from typing import Any
from langchain_text_splitters.base import Language

from app.models.recursive_splitter import RecursiveCharacterTextSplitter


class TextSplitter(RecursiveCharacterTextSplitter):

    def __init__(self, language:Language,  **kwargs: Any) -> None:
        separators = self.get_separators_for_language(language)
        super().__init__(separators=separators, **kwargs)