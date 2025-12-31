from dotenv import load_dotenv
load_dotenv()
import os
from typing import List, Dict

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-8b-8192"  # Fast and free tier friendly

# JWT Secret for authentication
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Predefined Career Goals with skill templates
CAREER_GOALS = {
    "Web Developer": {
        "beginner": [
            {"name": "HTML Basics", "stage": "Beginner", "hours": 10},
            {"name": "CSS Fundamentals", "stage": "Beginner", "hours": 15},
            {"name": "JavaScript Basics", "stage": "Beginner", "hours": 20},
            {"name": "Responsive Design", "stage": "Beginner", "hours": 12},
            {"name": "Git & GitHub", "stage": "Beginner", "hours": 8},
            {"name": "Frontend Framework (React/Vue)", "stage": "Intermediate", "hours": 30},
            {"name": "Backend Basics (Node.js/Python)", "stage": "Intermediate", "hours": 25},
            {"name": "Databases (SQL)", "stage": "Intermediate", "hours": 20},
            {"name": "REST APIs", "stage": "Intermediate", "hours": 15},
            {"name": "Deployment & Hosting", "stage": "Intermediate", "hours": 10}
        ],
        "intermediate": [
            {"name": "Advanced JavaScript (ES6+)", "stage": "Intermediate", "hours": 20},
            {"name": "State Management (Redux/Vuex)", "stage": "Intermediate", "hours": 15},
            {"name": "Backend Framework (Express/FastAPI)", "stage": "Intermediate", "hours": 25},
            {"name": "Authentication & Security", "stage": "Advanced", "hours": 20},
            {"name": "Database Design & Optimization", "stage": "Advanced", "hours": 18},
            {"name": "Testing (Unit & Integration)", "stage": "Advanced", "hours": 15},
            {"name": "CI/CD Pipelines", "stage": "Advanced", "hours": 12},
            {"name": "Docker & Containers", "stage": "Advanced", "hours": 20},
            {"name": "Cloud Services (AWS/GCP)", "stage": "Advanced", "hours": 25},
            {"name": "Performance Optimization", "stage": "Advanced", "hours": 15}
        ]
    },
    "Data Analyst": {
        "beginner": [
            {"name": "Excel Fundamentals", "stage": "Beginner", "hours": 15},
            {"name": "Statistics Basics", "stage": "Beginner", "hours": 20},
            {"name": "SQL for Data Analysis", "stage": "Beginner", "hours": 25},
            {"name": "Python Basics", "stage": "Beginner", "hours": 20},
            {"name": "Data Visualization Basics", "stage": "Beginner", "hours": 12},
            {"name": "Pandas & NumPy", "stage": "Intermediate", "hours": 25},
            {"name": "Data Cleaning Techniques", "stage": "Intermediate", "hours": 18},
            {"name": "Tableau/Power BI", "stage": "Intermediate", "hours": 20},
            {"name": "Statistical Analysis", "stage": "Intermediate", "hours": 22},
            {"name": "Business Intelligence Concepts", "stage": "Intermediate", "hours": 15}
        ],
        "intermediate": [
            {"name": "Advanced SQL Queries", "stage": "Intermediate", "hours": 20},
            {"name": "Python Data Analysis Libraries", "stage": "Intermediate", "hours": 25},
            {"name": "Machine Learning Basics", "stage": "Advanced", "hours": 30},
            {"name": "A/B Testing & Experimentation", "stage": "Advanced", "hours": 18},
            {"name": "Big Data Tools (Spark)", "stage": "Advanced", "hours": 25},
            {"name": "Advanced Data Visualization", "stage": "Advanced", "hours": 15},
            {"name": "Predictive Analytics", "stage": "Advanced", "hours": 20},
            {"name": "Data Warehousing", "stage": "Advanced", "hours": 18},
            {"name": "ETL Processes", "stage": "Advanced", "hours": 15},
            {"name": "Dashboard Design & Strategy", "stage": "Advanced", "hours": 12}
        ]
    },
    "App Developer": {
        "beginner": [
            {"name": "Programming Fundamentals", "stage": "Beginner", "hours": 20},
            {"name": "Mobile UI/UX Basics", "stage": "Beginner", "hours": 15},
            {"name": "Choose Platform (iOS/Android)", "stage": "Beginner", "hours": 10},
            {"name": "Swift/Kotlin Basics", "stage": "Beginner", "hours": 30},
            {"name": "Mobile App Architecture", "stage": "Beginner", "hours": 18},
            {"name": "API Integration", "stage": "Intermediate", "hours": 20},
            {"name": "Local Data Storage", "stage": "Intermediate", "hours": 15},
            {"name": "Navigation Patterns", "stage": "Intermediate", "hours": 12},
            {"name": "Testing Mobile Apps", "stage": "Intermediate", "hours": 15},
            {"name": "App Store Deployment", "stage": "Intermediate", "hours": 10}
        ],
        "intermediate": [
            {"name": "Cross-Platform Development (React Native/Flutter)", "stage": "Intermediate", "hours": 35},
            {"name": "Advanced State Management", "stage": "Intermediate", "hours": 18},
            {"name": "Push Notifications", "stage": "Advanced", "hours": 12},
            {"name": "In-App Purchases", "stage": "Advanced", "hours": 15},
            {"name": "App Performance Optimization", "stage": "Advanced", "hours": 20},
            {"name": "Security Best Practices", "stage": "Advanced", "hours": 18},
            {"name": "Offline Functionality", "stage": "Advanced", "hours": 15},
            {"name": "App Analytics Integration", "stage": "Advanced", "hours": 10},
            {"name": "CI/CD for Mobile Apps", "stage": "Advanced", "hours": 15},
            {"name": "Advanced Animation & Gestures", "stage": "Advanced", "hours": 20}
        ]
    }
}

def get_available_career_goals() -> List[str]:
    """Return list of available career goals"""
    return list(CAREER_GOALS.keys())

def get_roadmap_template(career_goal: str, learning_level: str) -> List[Dict]:
    """Get skill template for a specific career goal and level"""
    level_key = learning_level.lower()
    
    if career_goal not in CAREER_GOALS:
        return []
    
    if level_key not in CAREER_GOALS[career_goal]:
        return []
    
    return CAREER_GOALS[career_goal][level_key]