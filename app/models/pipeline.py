from abc import ABC
from typing import Dict, Any, TypeVar, List

from pydantic.v1 import BaseModel

from app.llms.chat.generic_chat import generic_chat
from app.llms.chat.json_response import get_json_response
from typing import Type

T = TypeVar('T', bound=BaseModel)
class Pipeline(BaseModel, ABC):
    def template(self, **kwargs) -> str:
        """Define the template that is sent to the AI model"""
        pass

    async def execute_flow_dict(self, **kwargs) -> Dict[str, Any]:
        template = self.template(**kwargs)
        response = await get_json_response(
            template,
            system_message="You are an AI assistant designed to provide contextual summaries of code."
        )
        return response

    async def execute_flow_str(self, *args)->str:
        template = self.template(*args)
        response = await generic_chat(
            template,
            system_message="You are an AI assistant designed to provide contextual summaries of code."
        )
        return response

    async def execute_flow_model(self, class_type: Type[T], *args) -> List[T] | T:
        """Execute flow for templates that return in JSON format attributes of a model or list of models."""
        template = self.template(*args)
        response = await get_json_response(
            template,
            system_message="You are an AI assistant designed to provide contextual summaries of code."
        )

        keys = list(response.keys())
        if len(keys) == 1:
            data = response[keys[0]]
            if isinstance(data, list):
                li = []
                for item in data:
                    li.append(class_type.model_validate(item))
                return li

        return class_type.model_validate(response)