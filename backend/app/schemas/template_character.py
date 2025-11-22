"""Schemas for template character API."""

from typing import Optional

from pydantic import BaseModel


class CharacterPose(BaseModel):
    """Schema for a character pose."""

    id: str
    thumbnail_url: str
    image_url: str


class TemplateCharacter(BaseModel):
    """Schema for a template character."""

    id: str
    name: str
    description: Optional[str] = None
    poses: list[CharacterPose]
    default_pose: str


class TemplateCharacterListResponse(BaseModel):
    """Response schema for listing template characters."""

    templates: list[TemplateCharacter]


class TemplateCharacterApply(BaseModel):
    """Request schema for applying a template character to a song."""

    character_id: str
    pose: Optional[str] = "pose-a"

