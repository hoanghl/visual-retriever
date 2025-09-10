"""
Contain Models (Entities) mapping data in database
"""

from datetime import datetime
from enum import Enum
from typing import List

from sqlmodel import ARRAY, Column, Field, Integer, Relationship, SQLModel


class RESOURCE_TYPE(Enum):
    IMAGE = (1, "image")
    VIDEO = (2, "video")

    def __init__(self, value, val):
        self._value_ = value
        self.val = val


class ResourceType(SQLModel, table=True):
    __tablename__ = "resource_type"

    id: int = Field(default=None, primary_key=True)
    type: str


class KeywordCategory(SQLModel, table=True):
    __tablename__ = "keyword_category"

    id: int = Field(default=None, primary_key=True)
    category_name: str


class Keyword(SQLModel, table=True):
    __tablename__ = "keyword"

    id: int = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="keyword_category.id")
    word: str

    category: KeywordCategory = Relationship()


class Resource(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    resource_type: int = Field(foreign_key="resource_type.id")
    name: str
    date_added: datetime = Field(default_factory=datetime.now)
    keywords: List[int] = Field(sa_column=Column(ARRAY(Integer)))

    res_type: ResourceType = Relationship()

    class Config:
        arbitrary_types_allowed = True
