from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from level_generator import generate_level_roadmap
from datetime import timedelta
import json
from config import GROQ_API_KEY

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
#admin
@app.get("/admin/users")
def get_all_users():
    """Get all registered users (Admin only)"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, created_at FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"users": users}
# ============ AUTH ENDPOINTS ============

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister):
    """Register a new user"""
    try:
        user = create_user(user_data.username, user_data.password, user_data.email)
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "created_at": str(user["created_at"])
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Register error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

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

# ============ HELPER FUNCTION FOR ROADMAP RETRIEVAL ============

def _get_user_roadmaps(user_id: int):
    """Helper function to get all roadmaps for a user (without dependency injection)"""
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
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
    return _get_user_roadmaps(current_user["id"])

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
    
    roadmaps = _get_user_roadmaps(current_user["id"])
    
    total_skills = sum(len(r["skills"]) for r in roadmaps)
    completed_skills = sum(
        sum(1 for s in r["skills"] if s["status"] == "COMPLETED") 
        for r in roadmaps
    )
    in_progress_skills = sum(
        sum(1 for s in r["skills"] if s["status"] == "IN_PROGRESS") 
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

@app.post("/roadmaps/create-levels", status_code=status.HTTP_201_CREATED)
def create_level_roadmap(
    roadmap_data: RoadmapCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    🎮 Create NEW level-based roadmap (Game-style)
    This is the NEW endpoint that generates levels instead of skills
    """
    
    # Validate career goal
    if roadmap_data.career_goal not in get_available_career_goals():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid career goal. Choose from: {get_available_career_goals()}"
        )
    
    # Get skill template (reuse existing config)
    skills_template = get_roadmap_template(
        roadmap_data.career_goal, 
        roadmap_data.learning_level
    )
    
    if not skills_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid learning level"
        )
    
    print(f"🎮 Generating level-based roadmap for {roadmap_data.career_goal}...")
    
    # Convert skills to levels using our generator
    level_roadmap = generate_level_roadmap(
        skills_template,
        roadmap_data.career_goal,
        roadmap_data.learning_level
    )
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Create roadmap entry with metadata
    cursor.execute(
        """INSERT INTO roadmaps (user_id, career_goal, learning_level, existing_skills, metadata) 
           VALUES (?, ?, ?, ?, ?)""",
        (
            current_user["id"],
            roadmap_data.career_goal,
            roadmap_data.learning_level,
            json.dumps(roadmap_data.existing_skills or []),
            json.dumps(level_roadmap)  # Store entire level structure as JSON
        )
    )
    
    roadmap_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ Level roadmap created! ID: {roadmap_id}, Total levels: {len(level_roadmap['levels'])}")
    
    return {
        "roadmap_id": roadmap_id,
        "message": "🎮 Level roadmap created successfully!",
        "total_levels": level_roadmap["roadmap"]["total_levels"],
        "estimated_days": level_roadmap["roadmap"]["estimated_days"]
    }


@app.get("/roadmaps/{roadmap_id}/levels")
def get_roadmap_levels(
    roadmap_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    📊 Get level-based roadmap with current progress
    This endpoint returns the game-like level structure
    """
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get roadmap
    cursor.execute(
        "SELECT * FROM roadmaps WHERE id = ? AND user_id = ?",
        (roadmap_id, current_user["id"])
    )
    roadmap = cursor.fetchone()
    
    if not roadmap:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found"
        )
    
    # Check if this is a level-based roadmap
    if not roadmap["metadata"]:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This is not a level-based roadmap. Use /roadmaps/my-roadmaps instead."
        )
    
    # Parse level data from metadata
    level_data = json.loads(roadmap["metadata"])
    
    # Get user progress from level_progress table
    cursor.execute(
        """SELECT level_number, completed_at, xp_earned, time_spent_minutes 
           FROM level_progress 
           WHERE roadmap_id = ?
           ORDER BY level_number""",
        (roadmap_id,)
    )
    progress_records = cursor.fetchall()
    conn.close()
    
    # Build progress dictionary
    completed_levels = {}
    total_xp = 0
    total_time = 0
    
    for record in progress_records:
        level_num = record["level_number"]
        completed_levels[level_num] = {
            "completed_at": record["completed_at"],
            "xp_earned": record["xp_earned"],
            "time_spent": record["time_spent_minutes"]
        }
        total_xp += record["xp_earned"]
        total_time += record["time_spent_minutes"]
    
    # Update level statuses based on progress
    current_level_number = len(completed_levels) + 1
    
    for level in level_data["levels"]:
        level_num = level["level_number"]
        
        if level_num in completed_levels:
            level["status"] = "completed"
            level["completed_at"] = completed_levels[level_num]["completed_at"]
        elif level_num == current_level_number:
            level["status"] = "unlocked"
        else:
            level["status"] = "locked"
    
    # Update stats
    level_data["stats"]["levels_completed"] = len(completed_levels)
    level_data["stats"]["total_xp"] = total_xp
    level_data["stats"]["time_spent_minutes"] = total_time
    
    # Update roadmap progress
    progress_percentage = (len(completed_levels) / len(level_data["levels"])) * 100
    level_data["roadmap"]["progress_percentage"] = round(progress_percentage, 2)
    level_data["roadmap"]["current_level"] = current_level_number
    
    # Calculate streak (simplified - just check if activity in last 24 hours)
    from datetime import datetime, timedelta
    if progress_records:
        last_completion = datetime.fromisoformat(progress_records[-1]["completed_at"])
        now = datetime.now()
        if (now - last_completion).days < 2:
            level_data["stats"]["current_streak"] = 1  # Simplified streak
    
    return level_data


@app.post("/roadmaps/{roadmap_id}/levels/{level_number}/complete")
def complete_level(
    roadmap_id: int,
    level_number: int,
    current_user: dict = Depends(get_current_user)
):
    """
    ✅ Mark a level as completed
    This unlocks the next level and awards XP
    """
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute(
        "SELECT * FROM roadmaps WHERE id = ? AND user_id = ?",
        (roadmap_id, current_user["id"])
    )
    roadmap = cursor.fetchone()
    
    if not roadmap:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Get level data
    level_data = json.loads(roadmap["metadata"])
    current_level = next(
        (l for l in level_data["levels"] if l["level_number"] == level_number), 
        None
    )
    
    if not current_level:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Level not found"
        )
    
    # Check if level is already completed
    cursor.execute(
        "SELECT * FROM level_progress WHERE roadmap_id = ? AND level_number = ?",
        (roadmap_id, level_number)
    )
    
    if cursor.fetchone():
        conn.close()
        return {
            "message": "Level already completed",
            "xp_earned": 0
        }
    
    # Record completion
    xp_reward = current_level["xp_reward"]
    
    cursor.execute(
        """INSERT INTO level_progress 
           (roadmap_id, level_number, xp_earned, time_spent_minutes)
           VALUES (?, ?, ?, ?)""",
        (roadmap_id, level_number, xp_reward, current_level["estimated_minutes"])
    )
    
    # Update last_activity
    cursor.execute(
        "UPDATE roadmaps SET last_activity = CURRENT_TIMESTAMP WHERE id = ?",
        (roadmap_id,)
    )
    
    conn.commit()
    conn.close()
    
    # Check if it's a boss level (awards badge)
    badge = None
    if current_level["level_type"] == "boss":
        badge = current_level.get("badge_earned", "Master Badge 🏆")
    
    return {
        "message": "🎉 Level completed!",
        "level_number": level_number,
        "xp_earned": xp_reward,
        "next_level": level_number + 1,
        "badge_earned": badge,
        "level_type": current_level["level_type"]
    }


@app.get("/dashboard-levels")
def get_dashboard_levels(current_user: dict = Depends(get_current_user)):
    """
    📊 Get dashboard with level-based roadmaps
    Similar to /dashboard but returns level format
    """
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get all user roadmaps
    cursor.execute(
        "SELECT * FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC",
        (current_user["id"],)
    )
    roadmaps = cursor.fetchall()
    
    result = []
    total_xp = 0
    total_levels_completed = 0
    
    for roadmap in roadmaps:
        if not roadmap["metadata"]:
            continue  # Skip old-style roadmaps
        
        level_data = json.loads(roadmap["metadata"])
        
        # Get progress for this roadmap
        cursor.execute(
            "SELECT COUNT(*) as completed, SUM(xp_earned) as xp FROM level_progress WHERE roadmap_id = ?",
            (roadmap["id"],)
        )
        stats = cursor.fetchone()
        
        completed = stats["completed"] or 0
        xp = stats["xp"] or 0
        
        total_xp += xp
        total_levels_completed += completed
        
        result.append({
            "roadmap_id": roadmap["id"],
            "career_goal": roadmap["career_goal"],
            "learning_level": roadmap["learning_level"],
            "total_levels": level_data["roadmap"]["total_levels"],
            "levels_completed": completed,
            "current_level": completed + 1,
            "progress_percentage": (completed / level_data["roadmap"]["total_levels"]) * 100,
            "total_xp": xp,
            "created_at": roadmap["created_at"]
        })
    
    conn.close()
    
    return {
        "user": {
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user["email"]
        },
        "roadmaps": result,
        "total_xp": total_xp,
        "total_levels_completed": total_levels_completed
    }


@app.post("/api/ai-chat")
async def ai_chat_proxy(
    message: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Proxy AI chat requests through backend (more secure)
    This keeps the API key completely hidden from frontend
    """
    import requests
    
    # Get user context
    roadmaps = _get_user_roadmaps(current_user["id"])
    
    # Build context-aware system prompt
    context = ""
    if roadmaps:
        latest_roadmap = roadmaps[0]
        context = f"User is learning {latest_roadmap['career_goal']} at {latest_roadmap['learning_level']} level."
    
    system_prompt = f"""You are a helpful programming and tech education tutor. 
    {context}
    Provide clear, practical, and encouraging explanations. 
    Keep responses conversational and under 200 words unless asked for detailed explanations."""
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "response": data["choices"][0]["message"]["content"],
                "model": "llama3-8b-8192"
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="AI service error"
            )
            
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service timeout"
        )
    except Exception as e:
        print(f"AI chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process AI request"
        )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)