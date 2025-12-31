from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ============ USER MODELS ============

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    created_at: str

# ============ ROADMAP MODELS ============

class RoadmapCreate(BaseModel):
    career_goal: str
    learning_level: str = Field(..., pattern="^(Beginner|Intermediate)$")
    existing_skills: Optional[List[str]] = []

class SkillResponse(BaseModel):
    id: int
    skill_name: str
    learning_stage: str
    order_index: int
    why_important: Optional[str]
    estimated_hours: Optional[int]
    status: str  # NOT_STARTED, IN_PROGRESS, COMPLETED
    status_id: int  # For updating status

class RoadmapResponse(BaseModel):
    id: int
    user_id: int
    career_goal: str
    learning_level: str
    existing_skills: List[str]
    created_at: str
    skills: List[SkillResponse]
    progress_percentage: float

# ============ SKILL STATUS MODELS ============

class SkillStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(NOT_STARTED|IN_PROGRESS|COMPLETED)$")

class SkillStatusResponse(BaseModel):
    id: int
    skill_id: int
    status: str
    updated_at: str

# ============ DASHBOARD MODELS ============

class DashboardResponse(BaseModel):
    user: UserResponse
    roadmaps: List[RoadmapResponse]
    total_skills: int
    completed_skills: int
    in_progress_skills: int
    overall_progress: float

# ============ AUTH MODELS ============

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None