from __future__ import annotations

from typing import Any
from langchain_text_splitters.base import Language

from app.models.splitters.recursive_splitter import RecursiveCharacterTextSplitter


class TextSplitter(RecursiveCharacterTextSplitter):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)