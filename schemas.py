from pydantic import (
    BaseModel
)
from typing import Optional, Union


class Parameter(BaseModel):
    value: Union[str, list[str]]
    value_type: str
    description: str
    example_value: Optional[Union[str, list[str]]] = None
    from_conversation: bool
    value_options: Optional[list[str]] = None


class CapitalizerConfig(BaseModel):
    target_text: Parameter 