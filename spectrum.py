from typing import Dict
from typing import ForwardRef
from typing import List

from pydantic import BaseModel
from pydantic import Field


class SpectrumUnit(BaseModel):
    name: str = ""
    url: str = ""
    definition: str = ""
    how_to_record: str = ""
    examples: List[str] = []
    use: str = ""
    information_group: str = ""
    members: Dict[str, ForwardRef("SpectrumUnit")] = Field(default_factory=dict)


class SpectrumInformationGroup(BaseModel):
    name: str = ""
    description: str = ""
    url: str = ""
    members: Dict[str, SpectrumUnit] = Field(default_factory=dict)


class SpectrumInformationGroupType(BaseModel):
    name: str = ""
    description: str = ""
    url: str = ""
    members: Dict[str, SpectrumInformationGroup] = Field(default_factory=dict)
