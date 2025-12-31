"""
Quick test script to verify API functionality
Run this after starting the server: python main.py
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def test_api():
    """Run through complete API workflow"""
    
    print("🚀 Starting API Test...\n")
    
    # 1. Check server is running
    print("1️⃣ Checking server...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print_response("Root Endpoint", response)
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running! Start it with: python main.py")
        return
    
    # 2. Get available career goals
    print("\n2️⃣ Getting career goals...")
    response = requests.get(f"{BASE_URL}/career-goals")
    print_response("Career Goals", response)
    
    # 3. Register a test user
    print("\n3️⃣ Registering user...")
    register_data = {
        "username": "demo_user",
        "password": "demo123",
        "email": "demo@example.com"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print_response("User Registration", response)
    
    if response.status_code == 400:
        print("ℹ️  User already exists, trying to login...")
    
    # 4. Login
    print("\n4️⃣ Logging in...")
    login_data = {
        "username": "demo_user",
        "password": "demo123"
    }
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data
    )
    print_response("Login", response)
    
    if response.status_code != 200:
        print("❌ Login failed!")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 5. Get current user
    print("\n5️⃣ Getting user info...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print_response("Current User", response)
    
    # 6. Create a roadmap
    print("\n6️⃣ Creating roadmap...")
    print("⏳ This may take a few seconds (generating AI explanations)...")
    roadmap_data = {
        "career_goal": "Web Developer",
        "learning_level": "Beginner",
        "existing_skills": ["HTML Basics"]
    }
    response = requests.post(
        f"{BASE_URL}/roadmaps/create",
        json=roadmap_data,
        headers=headers
    )
    print_response("Roadmap Creation", response)
    
    if response.status_code != 201:
        print("❌ Roadmap creation failed!")
        return
    
    roadmap = response.json()
    first_skill_status_id = roadmap["skills"][0]["status_id"]
    
    # 7. Update a skill status
    print("\n7️⃣ Updating skill status...")
    status_update = {"status": "IN_PROGRESS"}
    response = requests.patch(
        f"{BASE_URL}/skills/{first_skill_status_id}/update",
        json=status_update,
        headers=headers
    )
    print_response("Skill Status Update", response)
    
    # 8. Get dashboard
    print("\n8️⃣ Getting dashboard...")
    response = requests.get(f"{BASE_URL}/dashboard", headers=headers)
    print_response("Dashboard", response)
    
    print("\n" + "="*60)
    print("✅ API Test Complete!")
    print("="*60)
    print("\n🎉 All endpoints working! Check http://localhost:8000/docs")

if __name__ == "__main__":
    test_api()