from abc import ABC, abstractmethod
from typing import Any, TypeVar, Tuple, Optional, List, Dict, AsyncGenerator

from pydantic.v1 import BaseModel

from app.databases.mongo_db import MongoDBDatabase
from app.llms.chat.generic_chat import generic_chat
from app.llms.chat.json_response import get_json_response
from typing import Type

from app.llms.stream_chat.generic_stream_chat import generic_stream_chat

T = TypeVar('T', bound=BaseModel)


class Pipeline(ABC):
    mdb: Optional[MongoDBDatabase] = None

    def __init__(self, mdb: Optional[MongoDBDatabase] = None):
        self.mdb = mdb

    @property
    @abstractmethod
    def response_type(self) -> str:
        """Return the response format type: 'str', 'dict', 'model', or 'stream'."""
        pass

    @abstractmethod
    def template(self, **kwargs) -> str:
        """Define the template that is sent to the AI model"""
        pass

    async def execute(self, **kwargs) -> Any:
        template = self.template(**kwargs)

        if self.response_type == "str":
            processor = self._str_processor
        elif self.response_type == "dict":
            processor = self._dict_processor
        elif self.response_type == "model":
            processor = self._model_processor
        else:
            raise ValueError(f"Unsupported response type: {self.response_type}")

        raw_response, processed_response = await processor(template, **kwargs)
        return processed_response

    async def stream_execute(
            self,
            system_message: str = "...",
            history: List[Dict[str, str]] = None,
            **kwargs
    ) -> AsyncGenerator[Any, None]:
        template = self.template(**kwargs)

        if self.response_type == "stream":
            async for data in generic_stream_chat(
                    message=template,
                    system_message=system_message,
                    history=history,
                    mdb=self.mdb,
            ):
                yield data

    @staticmethod
    async def _str_processor(template: str, **_) -> Tuple[str, str]:
        raw = await generic_chat(template, system_message="...")
        return raw, raw

    @staticmethod
    async def _dict_processor(template: str, **_) -> Tuple[dict, dict]:
        raw = await get_json_response(template, system_message="...")
        return raw, raw

    @staticmethod
    async def _model_processor(template: str, class_type: Type[T], **_) -> Tuple[dict, T]:
        raw = await get_json_response(template, system_message="...")
        return raw, class_type.model_validate(raw)
