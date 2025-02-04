import logging
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Tuple, Optional, List, Dict, AsyncGenerator

from pydantic.v1 import BaseModel

from app.databases.mongo_db import MongoDBDatabase
from typing import Type

from app.llms.models import ChatLLM, StreamChatLLM
from app.utils.json_extraction import trim_and_load_json

T = TypeVar('T', bound=BaseModel)


class Pipeline(ABC):
    mdb: Optional[MongoDBDatabase] = None

    def __init__(self, mdb: Optional[MongoDBDatabase] = None):
        self.mdb = mdb

    @abstractmethod
    def template(self, **kwargs) -> str:
        """Define the template that is sent to the AI model"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass


class ChatPipeline(Pipeline):
    chat_llm: ChatLLM

    def __init__(self, chat_llm: ChatLLM, mdb: Optional[MongoDBDatabase] = None):
        super().__init__(mdb)
        self.chat_llm = chat_llm

    @property
    @abstractmethod
    def response_type(self) -> str:
        """Return the response format type: 'str', 'dict', 'model', or 'stream'."""
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

    async def _str_processor(self, template: str, **_) -> Tuple[str, str]:
        raw = await self.chat_llm.generate(template, system_message="...")
        return raw, raw

    async def _dict_processor(self, template: str, **_) -> Tuple[str, dict]:
        json_data = {}
        raw = ""
        is_finished = False
        tries = 0
        while not is_finished:
            if tries > 0:
                logging.warning(f"Chat not returning as expected. it: {tries}")

            if tries > 3:
                if tries > 0:
                    logging.warning("Chat not returning as expected.")
                raise Exception()

            raw = await self.chat_llm.generate(template, system_message="...")

            is_finished, json_data = await trim_and_load_json(input_string=raw)
            tries += 1
        return raw, json_data

    async def _model_processor(self, template: str, class_type: Type[T], **_) -> Tuple[str, T]:
        raw, json_data = await self._dict_processor(template, system_message="...")
        return raw, class_type.model_validate(json_data)



class StreamPipeline(Pipeline, ABC):
    stream_chat_llm: StreamChatLLM

    def __init__(self, stream_chat_llm: StreamChatLLM, mdb: Optional[MongoDBDatabase] = None):
        super().__init__(mdb)
        self.stream_chat_llm = stream_chat_llm

    async def execute(
            self,
            system_message: str = "...",
            history: List[Dict[str, str]] = None,
            **kwargs
    ) -> AsyncGenerator[Any, None]:
        template = self.template(**kwargs)

        async for data in self.stream_chat_llm.generate(
                message=template,
                system_message=system_message,
                history=history,
        ):
            yield data
