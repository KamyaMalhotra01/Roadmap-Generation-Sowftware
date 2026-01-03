"""
Quick fix script - automatically fixes common issues
Run: python quick_fix.py
"""

import os
import subprocess
import sys

print("🔧 QUICK FIX SCRIPT")
print("=" * 70)
print()

def run_command(cmd, description):
    """Run a shell command"""
    print(f"📌 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            return True
        else:
            print(f"   ⚠️  Warning: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

# 1. Fix bcrypt
print("1️⃣ FIXING BCRYPT VERSION")
print("-" * 70)
run_command("pip uninstall bcrypt -y", "Uninstalling old bcrypt")
run_command("pip install bcrypt==4.0.1", "Installing bcrypt 4.0.1")
print()

# 2. Install missing dependencies
print("2️⃣ INSTALLING DEPENDENCIES")
print("-" * 70)
run_command("pip install python-dotenv", "Installing python-dotenv")
run_command("pip install -r requirements.txt", "Installing all requirements")
print()

# 3. Check .env file
print("3️⃣ CHECKING .ENV FILE")
print("-" * 70)

if not os.path.exists('.env') or os.path.getsize('.env') == 0:
    print("   Creating .env file...")
    with open('.env', 'w') as f:
        f.write("# GROQ API Configuration\n")
        f.write("# Get your free API key at: https://console.groq.com\n")
        f.write("GROQ_API_KEY=your-groq-api-key-here\n")
        f.write("\n")
        f.write("# JWT Secret for Authentication\n")
        f.write("JWT_SECRET=super-secret-jwt-key-12345\n")
    print("   ✅ Created .env file")
    print("   ⚠️  IMPORTANT: Edit .env and add your Groq API key!")
else:
    print("   ✅ .env file exists")

print()

# 4. Initialize database
print("4️⃣ INITIALIZING DATABASE")
print("-" * 70)

if os.path.exists('learning_roadmap.db'):
    response = input("   Database exists. Reset it? (y/n): ")
    if response.lower() == 'y':
        os.remove('learning_roadmap.db')
        print("   🗑️  Deleted old database")

run_command("python database.py", "Creating database")
print()

# 5. Verify setup
print("5️⃣ VERIFYING SETUP")
print("-" * 70)

try:
    # Check bcrypt
    import bcrypt
    print(f"   ✅ bcrypt version: {bcrypt.__version__}")
    
    # Check environment
    from dotenv import load_dotenv
    load_dotenv()
    groq_key = os.getenv("GROQ_API_KEY")
    jwt_secret = os.getenv("JWT_SECRET")
    
    if groq_key and groq_key != "your-groq-api-key-here":
        print(f"   ✅ GROQ_API_KEY is set")
    else:
        print(f"   ⚠️  GROQ_API_KEY not set - edit .env file")
    
    if jwt_secret:
        print(f"   ✅ JWT_SECRET is set")
    else:
        print(f"   ⚠️  JWT_SECRET not set - edit .env file")
    
    # Check database
    if os.path.exists('learning_roadmap.db'):
        print(f"   ✅ Database file exists")
    else:
        print(f"   ❌ Database file missing")
        
except Exception as e:
    print(f"   ❌ Verification error: {str(e)}")

print()

# Summary
print("=" * 70)
print("✨ QUICK FIX COMPLETE!")
print("=" * 70)
print()
print("📋 NEXT STEPS:")
print()
print("1. Edit .env file and add your Groq API key:")
print("   Get it from: https://console.groq.com")
print()
print("2. Start the server:")
print("   python -m uvicorn main:app --reload")
print()
print("3. Test registration:")
print("   Visit: http://localhost:8000/docs")
print("   Try: POST /auth/register")
print()
print("4. Run diagnostic:")
print("   python diagnose.py")
print()