from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import json

from database import Database
from models import *
from auth import (
    create_user, 
    authenticate_user, 
    create_access_token, 
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from config import get_available_career_goals, get_roadmap_template
from ai_service import ai_service

# Initialize FastAPI app
app = FastAPI(
    title="Learning Roadmap Tracker API",
    description="API for personalized learning roadmap generation and tracking",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database instance
db = Database()

# ============ ROOT ENDPOINT ============

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Learning Roadmap Tracker API",
        "docs": "/docs",
        "available_endpoints": {
            "auth": "/auth/register, /auth/login",
            "roadmaps": "/roadmaps/create, /roadmaps/my-roadmaps",
            "skills": "/skills/{skill_status_id}/update",
            "dashboard": "/dashboard"
        }
    }

# ============ AUTH ENDPOINTS ============

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister):
    """Register a new user"""
    user = create_user(user_data.username, user_data.password, user_data.email)
    
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"]
    }

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "created_at": current_user["created_at"]
    }

# ============ CAREER GOALS ENDPOINT ============

@app.get("/career-goals")
def get_career_goals():
    """Get available career goals"""
    return {
        "career_goals": get_available_career_goals(),
        "learning_levels": ["Beginner", "Intermediate"]
    }

# ============ ROADMAP ENDPOINTS ============

@app.post("/roadmaps/create", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
def create_roadmap(
    roadmap_data: RoadmapCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new learning roadmap"""
    
    # Validate career goal
    if roadmap_data.career_goal not in get_available_career_goals():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid career goal. Choose from: {get_available_career_goals()}"
        )
    
    # Get skill template
    skills_template = get_roadmap_template(
        roadmap_data.career_goal, 
        roadmap_data.learning_level
    )
    
    if not skills_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid learning level"
        )
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Create roadmap
    cursor.execute(
        """INSERT INTO roadmaps (user_id, career_goal, learning_level, existing_skills) 
           VALUES (?, ?, ?, ?)""",
        (
            current_user["id"],
            roadmap_data.career_goal,
            roadmap_data.learning_level,
            json.dumps(roadmap_data.existing_skills or [])
        )
    )
    
    roadmap_id = cursor.lastrowid
    
    # Generate AI explanations (in background for demo, can be async)
    print(f"🤖 Generating AI explanations for {len(skills_template)} skills...")
    explanations = ai_service.generate_batch_explanations(
        skills_template, 
        roadmap_data.career_goal
    )
    
    # Insert skills
    skills_data = []
    for idx, skill in enumerate(skills_template):
        cursor.execute(
            """INSERT INTO skills 
               (roadmap_id, skill_name, learning_stage, order_index, why_important, estimated_hours)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                roadmap_id,
                skill["name"],
                skill["stage"],
                idx,
                explanations.get(skill["name"], ""),
                skill.get("hours", None)
            )
        )
        
        skill_id = cursor.lastrowid
        
        # Create initial skill status
        cursor.execute(
            "INSERT INTO skill_status (skill_id, status) VALUES (?, 'NOT_STARTED')",
            (skill_id,)
        )
        
        status_id = cursor.lastrowid
        
        skills_data.append({
            "id": skill_id,
            "skill_name": skill["name"],
            "learning_stage": skill["stage"],
            "order_index": idx,
            "why_important": explanations.get(skill["name"], ""),
            "estimated_hours": skill.get("hours", None),
            "status": "NOT_STARTED",
            "status_id": status_id
        })
    
    conn.commit()
    
    # Fetch created roadmap
    cursor.execute("SELECT * FROM roadmaps WHERE id = ?", (roadmap_id,))
    roadmap = cursor.fetchone()
    
    conn.close()
    
    return {
        "id": roadmap["id"],
        "user_id": roadmap["user_id"],
        "career_goal": roadmap["career_goal"],
        "learning_level": roadmap["learning_level"],
        "existing_skills": json.loads(roadmap["existing_skills"]),
        "created_at": roadmap["created_at"],
        "skills": skills_data,
        "progress_percentage": 0.0
    }

@app.get("/roadmaps/my-roadmaps", response_model=List[RoadmapResponse])
def get_my_roadmaps(current_user: dict = Depends(get_current_user)):
    """Get all roadmaps for current user"""
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC",
        (current_user["id"],)
    )
    roadmaps = cursor.fetchall()
    
    result = []
    
    for roadmap in roadmaps:
        # Get skills with status
        cursor.execute("""
            SELECT s.*, ss.status, ss.id as status_id
            FROM skills s
            JOIN skill_status ss ON s.id = ss.skill_id
            WHERE s.roadmap_id = ?
            ORDER BY s.order_index
        """, (roadmap["id"],))
        
        skills = cursor.fetchall()
        
        skills_data = [
            {
                "id": skill["id"],
                "skill_name": skill["skill_name"],
                "learning_stage": skill["learning_stage"],
                "order_index": skill["order_index"],
                "why_important": skill["why_important"],
                "estimated_hours": skill["estimated_hours"],
                "status": skill["status"],
                "status_id": skill["status_id"]
            }
            for skill in skills
        ]
        
        # Calculate progress
        total = len(skills_data)
        completed = sum(1 for s in skills_data if s["status"] == "COMPLETED")
        progress = (completed / total * 100) if total > 0 else 0
        
        result.append({
            "id": roadmap["id"],
            "user_id": roadmap["user_id"],
            "career_goal": roadmap["career_goal"],
            "learning_level": roadmap["learning_level"],
            "existing_skills": json.loads(roadmap["existing_skills"]),
            "created_at": roadmap["created_at"],
            "skills": skills_data,
            "progress_percentage": round(progress, 2)
        })
    
    conn.close()
    
    return result

# ============ SKILL STATUS ENDPOINTS ============

@app.patch("/skills/{skill_status_id}/update", response_model=SkillStatusResponse)
def update_skill_status(
    skill_status_id: int,
    status_update: SkillStatusUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update skill completion status"""
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute("""
        SELECT ss.*, s.roadmap_id, r.user_id
        FROM skill_status ss
        JOIN skills s ON ss.skill_id = s.id
        JOIN roadmaps r ON s.roadmap_id = r.id
        WHERE ss.id = ?
    """, (skill_status_id,))
    
    skill_status = cursor.fetchone()
    
    if not skill_status:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill status not found"
        )
    
    if skill_status["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this skill"
        )
    
    # Update status
    cursor.execute(
        "UPDATE skill_status SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status_update.status, skill_status_id)
    )
    
    conn.commit()
    
    # Fetch updated status
    cursor.execute("SELECT * FROM skill_status WHERE id = ?", (skill_status_id,))
    updated_status = cursor.fetchone()
    
    conn.close()
    
    return {
        "id": updated_status["id"],
        "skill_id": updated_status["skill_id"],
        "status": updated_status["status"],
        "updated_at": updated_status["updated_at"]
    }

# ============ DASHBOARD ENDPOINT ============

@app.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Get complete dashboard data"""
    
    roadmaps = get_my_roadmaps(current_user)
    
    total_skills = sum(len(r.skills) for r in roadmaps)
    completed_skills = sum(
        sum(1 for s in r.skills if s.status == "COMPLETED") 
        for r in roadmaps
    )
    in_progress_skills = sum(
        sum(1 for s in r.skills if s.status == "IN_PROGRESS") 
        for r in roadmaps
    )
    
    overall_progress = (completed_skills / total_skills * 100) if total_skills > 0 else 0
    
    return {
        "user": {
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user["email"],
            "created_at": current_user["created_at"]
        },
        "roadmaps": roadmaps,
        "total_skills": total_skills,
        "completed_skills": completed_skills,
        "in_progress_skills": in_progress_skills,
        "overall_progress": round(overall_progress, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)