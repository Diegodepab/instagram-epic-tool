"""Strict boundary and domain models for Instagram relationship analysis."""

from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore")


class RawStringListItem(StrictModel):
    value: str | None = None
    href: str | None = None
    timestamp: int | None = None


class RawRelationship(StrictModel):
    title: str = ""
    string_list_data: list[RawStringListItem] = Field(default_factory=list)


class RawFollowingDocument(StrictModel):
    relationships_following: list[RawRelationship]


class NodeGroup(IntEnum):
    CENTRAL = 0
    MUTUAL = 1
    FAN = 2
    NON_FOLLOWER = 3


class UserNode(StrictModel):
    id: str = Field(min_length=1, max_length=30)
    username: str = Field(min_length=2, max_length=31)
    group: int = Field(ge=0, le=3)


class GraphLink(StrictModel):
    source: str = Field(min_length=1, max_length=30)
    target: str = Field(min_length=1, max_length=30)


class GraphData(StrictModel):
    nodes: list[UserNode]
    links: list[GraphLink]

