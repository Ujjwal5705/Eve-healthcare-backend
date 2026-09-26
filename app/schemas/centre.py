from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class TestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal


class TestCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: Decimal = Field(..., gt=0)


class CentreCreate(BaseModel):
    name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)


class CentreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    tests: List[TestOut] = []


class CentreOutBrief(BaseModel):
    """Used in list views where we don't want to load every nested test."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
