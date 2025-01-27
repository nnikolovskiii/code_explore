from abc import ABC, abstractmethod
from typing import Any, TypeVar, Tuple, Optional

from pydantic.v1 import BaseModel

from app.databases.mongo_db import MongoDBDatabase
from app.llms.chat.generic_chat import generic_chat
from app.llms.chat.json_response import get_json_response
from typing import Type

T = TypeVar('T', bound=BaseModel)


class Pipeline(ABC):
    mdb: Optional[MongoDBDatabase] = None

    def __init__(self, mdb: Optional[MongoDBDatabase]=None):
        self.mdb = mdb

    @property
    @abstractmethod
    def response_type(self) -> str:
        """Return the response format type: 'str', 'dict', or 'model'."""
        pass

    @abstractmethod
    def template(self, **kwargs) -> str:
        """Define the template that is sent to the AI model"""
        pass

    async def execute(self, **kwargs) -> Any:
        template = self.template(**kwargs)
        print(template)
        print("**************************************************************************")
        # Route based on response_type
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