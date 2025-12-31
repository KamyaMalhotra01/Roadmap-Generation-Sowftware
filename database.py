import sqlite3
from datetime import datetime
import json

class Database:
    def __init__(self, db_name="learning_roadmap.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Roadmaps table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roadmaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                career_goal TEXT NOT NULL,
                learning_level TEXT NOT NULL,
                existing_skills TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Skills table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roadmap_id INTEGER NOT NULL,
                skill_name TEXT NOT NULL,
                learning_stage TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                why_important TEXT,
                estimated_hours INTEGER,
                FOREIGN KEY (roadmap_id) REFERENCES roadmaps (id) ON DELETE CASCADE
            )
        ''')
        
        # Skill status tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id INTEGER NOT NULL,
                status TEXT DEFAULT 'NOT_STARTED',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE CASCADE,
                CHECK (status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED'))
            )
        ''')
        
        conn.commit()
        conn.close()
        print(" Database initialized successfully!")
    
    def reset_database(self):
        """Drop all tables and reinitialize (useful for development)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS skill_status")
        cursor.execute("DROP TABLE IF EXISTS skills")
        cursor.execute("DROP TABLE IF EXISTS roadmaps")
        cursor.execute("DROP TABLE IF EXISTS users")
        
        conn.commit()
        conn.close()
        
        self.init_database()
        print("Database reset complete!")

# Initialize database when this module is imported
if __name__ == "__main__":
    db = Database()
    print("Database setup complete!")