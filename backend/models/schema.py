"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class IssueCategory(str, Enum):
    """Supported issue categories."""
    WATER = "Water"
    FOOD = "Food"
    HEALTHCARE = "Healthcare"
    SHELTER = "Shelter"
    EDUCATION = "Education"
    OTHER = "Other"


class PriorityLevel(str, Enum):
    """Priority levels based on urgency score."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class NGOData(BaseModel):
    """Model for NGO data upload."""
    location: str = Field(..., description="Location name")
    issue: str = Field(..., description="Description of the issue")
    people_count: int = Field(..., ge=1, description="Number of people affected")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    contact_info: Optional[str] = Field(None, description="Contact information")


class ClassificationResult(BaseModel):
    """Model for AI classification result."""
    category: str = Field(..., description="Classified issue category")
    urgency: float = Field(..., ge=0, le=1, description="Urgency score (0-1)")
    priority: str = Field(..., description="Priority level")


class Volunteer(BaseModel):
    """Model for volunteer registration."""
    name: str = Field(..., description="Volunteer name")
    skills: List[str] = Field(..., description="List of skills")
    latitude: float = Field(..., ge=-90, le=90, description="Volunteer location")
    longitude: float = Field(..., ge=-180, le=180, description="Volunteer location")
    phone: Optional[str] = Field(None, description="Contact number")
    email: Optional[str] = Field(None, description="Email address")


class TaskAssignment(BaseModel):
    """Model for task assignment."""
    issue_id: str = Field(..., description="Firestore document ID of the issue")
    volunteer_id: str = Field(..., description="Firestore document ID of the volunteer")
    status: str = Field(default="assigned", description="Task status")


class MatchResult(BaseModel):
    """Model for volunteer-task match result."""
    issue_id: str
    issue_description: str
    volunteer_id: str
    volunteer_name: str
    match_score: float
    distance_km: float


class IssueResponse(BaseModel):
    """Model for issue retrieval response."""
    id: str
    location: str
    issue: str
    people_count: int
    latitude: float
    longitude: float
    category: str
    urgency: float
    priority: str
    status: str = "pending"
    assigned_volunteer: Optional[str] = None
