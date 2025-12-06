from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class PropertyLocation(BaseModel):
    rel_path: Path
    line_num: int


class CorrectnessExplanation(BaseModel):
    correctness: Literal["correct", "incorrect", "unknown"]
    explanation: str


class PropertyResult(BaseModel):
    property_location: PropertyLocation
    correctness_explanation: CorrectnessExplanation
    