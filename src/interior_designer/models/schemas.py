"""Data models for the interior designer application."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class DesignPreferences(BaseModel):
    """User's design preferences."""

    style: str | None = Field(
        default=None,
        description="Preferred design style (e.g., modern, rustic, minimalist)",
    )
    budget: Literal["low", "medium", "high"] | None = Field(
        default=None,
        description="Budget level for recommendations",
    )
    color_preferences: list[str] = Field(
        default_factory=list,
        description="Preferred colors",
    )
    specific_needs: str | None = Field(
        default=None,
        description="Specific requirements or needs",
    )


class DesignRequest(BaseModel):
    """Request for design analysis."""

    image_paths: list[Path] = Field(
        description="Paths to room images",
    )
    preferences: DesignPreferences = Field(
        default_factory=DesignPreferences,
        description="User's design preferences",
    )


class RoomAnalysis(BaseModel):
    """Analysis of a room from an image."""

    room_type: str = Field(description="Type of room (e.g., living room, bedroom)")
    current_style: str = Field(description="Current design style of the room")
    estimated_dimensions: str | None = Field(
        default=None, description="Estimated room dimensions"
    )
    existing_furniture: list[str] = Field(
        default_factory=list, description="List of existing furniture"
    )
    lighting_assessment: str = Field(description="Assessment of lighting conditions")
    color_palette: list[str] = Field(
        default_factory=list, description="Current color palette"
    )
    strengths: list[str] = Field(
        default_factory=list, description="Positive aspects of the room"
    )
    improvement_opportunities: list[str] = Field(
        default_factory=list, description="Areas that could be improved"
    )


class DesignRecommendation(BaseModel):
    """A design recommendation."""

    category: str = Field(
        description="Category (e.g., furniture, lighting, colors, decor)"
    )
    current_state: str = Field(description="Current state of this aspect")
    recommendation: str = Field(description="The recommendation")
    priority: Literal["high", "medium", "low"] = Field(
        description="Priority of this recommendation"
    )
    estimated_cost: str | None = Field(
        default=None, description="Estimated cost range"
    )
    product_suggestions: list[str] = Field(
        default_factory=list, description="Specific product suggestions"
    )
    image_edit_prompt: str | None = Field(
        default=None, description="Prompt for generating an image showing this change"
    )


class GeneratedImage(BaseModel):
    """A generated room visualization."""

    path: Path = Field(description="Path to the generated image")
    prompt_used: str = Field(description="The prompt used to generate the image")
    description: str = Field(description="Description of what the image shows")


class DesignReport(BaseModel):
    """Complete design report."""

    session_id: str = Field(description="Unique session identifier")
    original_images: list[Path] = Field(description="Paths to original images")
    room_analyses: list[RoomAnalysis] = Field(description="Analysis of each room")
    recommendations: list[DesignRecommendation] = Field(
        description="Design recommendations"
    )
    generated_images: list[GeneratedImage] = Field(
        default_factory=list, description="AI-generated visualizations"
    )
    summary: str = Field(description="Overall summary of recommendations")
