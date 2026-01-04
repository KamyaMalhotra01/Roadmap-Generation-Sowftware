# level_generator.py
"""
Converts skill-based roadmaps into level-based progression
Inspired by Duolingo + Candy Crush game design
"""

from typing import List, Dict
import json

class LevelGenerator:
    """Generate game-like levels from skill templates"""
    
    # Level type patterns (5-level cycles)
    LEVEL_PATTERN = [
        "basics",     # Level 1: Introduction
        "concept",    # Level 2: Core concept
        "practice",   # Level 3: Hands-on
        "challenge",  # Level 4: Quick test
        "boss"        # Level 5: Major project
    ]
    
    # Icons for each type
    LEVEL_ICONS = {
        "basics": ["🌱", "📖", "🔰", "💡"],
        "concept": ["🎨", "🧩", "⚙️", "🔬"],
        "practice": ["💼", "🛠️", "⚡", "🎯"],
        "challenge": ["🧠", "🎮", "⚔️", "🏃"],
        "boss": ["👑", "🏆", "💎", "🦸"]
    }
    
    # Task templates
    TASK_TEMPLATES = {
        "mcq": {
            "type": "mcq",
            "question": "What is {skill}?",
            "options": [],
            "hint": "Think about the main purpose"
        },
        "code": {
            "type": "code",
            "question": "Write code to demonstrate {skill}",
            "starter_code": "// Your code here",
            "hint": "Start with the basics"
        },
        "project": {
            "type": "project",
            "question": "Build a mini project using {skill}",
            "requirements": [],
            "submission_type": "link"
        }
    }
    
    def __init__(self):
        self.level_positions = self._generate_path_positions(20)
    
    def _generate_path_positions(self, total_levels: int) -> List[Dict[str, int]]:
        """Generate zigzag path positions like Candy Crush"""
        positions = []
        y_step = 100 / total_levels
        
        for i in range(total_levels):
            # Zigzag pattern
            if i % 4 == 0:
                x = 50  # Center
            elif i % 4 == 1:
                x = 30  # Left
            elif i % 4 == 2:
                x = 70  # Right
            else:
                x = 50  # Center
            
            y = i * y_step + 10
            positions.append({"x": x, "y": int(y)})
        
        return positions
    
    def convert_skills_to_levels(
        self, 
        skills: List[Dict], 
        career_goal: str,
        learning_level: str
    ) -> Dict:
        """
        Convert traditional skill list into level-based progression
        
        Args:
            skills: List of skills from original roadmap
            career_goal: Web Developer, Data Analyst, etc.
            learning_level: Beginner, Intermediate, Advanced
        
        Returns:
            Level-based roadmap JSON
        """
        
        # Adjust level granularity based on experience
        if learning_level == "Beginner":
            levels_per_skill = 2  # More granular
            time_per_level = 30
        elif learning_level == "Intermediate":
            levels_per_skill = 1  # Balanced
            time_per_level = 45
        else:  # Advanced
            levels_per_skill = 0.5  # Project-focused
            time_per_level = 90
        
        levels = []
        level_number = 1
        
        for skill_index, skill in enumerate(skills):
            # Determine how many levels for this skill
            num_levels = max(1, int(levels_per_skill))
            
            for sub_level in range(num_levels):
                # Determine level type (cycle through pattern)
                level_type_index = (level_number - 1) % len(self.LEVEL_PATTERN)
                level_type = self.LEVEL_PATTERN[level_type_index]
                
                # Get icon for this type
                icon_index = (level_number - 1) % len(self.LEVEL_ICONS[level_type])
                icon = self.LEVEL_ICONS[level_type][icon_index]
                
                # Generate level title
                if level_type == "boss":
                    title = f"🏆 BOSS: {skill['name']} Challenge"
                elif level_type == "challenge":
                    title = f"Quick {skill['name']} Quiz"
                elif level_type == "practice":
                    title = f"Build with {skill['name']}"
                elif level_type == "concept":
                    title = f"Understanding {skill['name']}"
                else:  # basics
                    title = f"Intro to {skill['name']}"
                
                # Simplify goal (one line only)
                goal = self._simplify_goal(skill['name'], level_type)
                
                # Get position
                position = self.level_positions[min(level_number - 1, len(self.level_positions) - 1)]
                
                # Generate resources (1-2 only)
                resources = self._generate_resources(skill['name'], level_type)
                
                # Generate task
                task = self._generate_task(skill['name'], level_type)
                
                # Calculate XP reward
                xp_reward = {
                    "basics": 100,
                    "concept": 150,
                    "practice": 200,
                    "challenge": 100,
                    "boss": 500
                }[level_type]
                
                # Determine initial status
                if level_number == 1:
                    status = "unlocked"
                else:
                    status = "locked"
                
                level = {
                    "level_number": level_number,
                    "level_type": level_type,
                    "title": title,
                    "status": status,
                    "icon": icon,
                    "position": position,
                    "estimated_minutes": time_per_level if level_type != "boss" else time_per_level * 2,
                    "goal": goal,
                    "resources": resources,
                    "task": task,
                    "xp_reward": xp_reward,
                    "completed_at": None
                }
                
                # Add boss-specific fields
                if level_type == "boss":
                    level["badge_earned"] = f"{skill['name']} Master 🏆"
                    level["description"] = "Your major project milestone!"
                
                levels.append(level)
                level_number += 1
        
        # Generate milestones (every 5 levels)
        milestones = self._generate_milestones(levels, career_goal)
        
        return {
            "roadmap": {
                "career_goal": career_goal,
                "learning_level": learning_level,
                "total_levels": len(levels),
                "estimated_days": self._calculate_days(levels),
                "current_level": 1,
                "progress_percentage": 0,
                "streak_days": 0
            },
            "levels": levels,
            "milestones": milestones,
            "stats": {
                "total_xp": 0,
                "levels_completed": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "badges_earned": [],
                "time_spent_minutes": 0
            }
        }
    
    def _simplify_goal(self, skill_name: str, level_type: str) -> str:
        """Generate one-line goal based on level type"""
        templates = {
            "basics": f"Learn the fundamentals of {skill_name}",
            "concept": f"Understand how {skill_name} works",
            "practice": f"Build something with {skill_name}",
            "challenge": f"Test your {skill_name} knowledge",
            "boss": f"Complete a real project using {skill_name}"
        }
        return templates[level_type]
    
    def _generate_resources(self, skill_name: str, level_type: str) -> List[Dict]:
        """Generate 1-2 learning resources"""
        resources = []
        
        if level_type in ["basics", "concept"]:
            resources.append({
                "type": "video",
                "title": f"{skill_name} Explained in 10 Minutes",
                "url": f"https://youtube.com/search?q={skill_name.replace(' ', '+')}+tutorial",
                "duration": "10 min"
            })
            resources.append({
                "type": "article",
                "title": f"{skill_name} Cheatsheet",
                "url": f"https://google.com/search?q={skill_name.replace(' ', '+')}+cheatsheet",
                "duration": "5 min read"
            })
        elif level_type == "practice":
            resources.append({
                "type": "interactive",
                "title": f"{skill_name} Playground",
                "url": f"https://codepen.io/search/pens?q={skill_name.replace(' ', '+')}",
                "duration": "Hands-on"
            })
        
        return resources[:2]  # Max 2 resources
    
    def _generate_task(self, skill_name: str, level_type: str) -> Dict:
        """Generate appropriate task for level type"""
        if level_type == "basics":
            return {
                "type": "mcq",
                "question": f"What is the main purpose of {skill_name}?",
                "options": [
                    "Option A (to be filled)",
                    "Option B (to be filled)",
                    "Option C (to be filled)",
                    "Option D (to be filled)"
                ],
                "correct_answer": "Option A (to be filled)",
                "hint": "Review the first resource"
            }
        
        elif level_type == "concept":
            return {
                "type": "code",
                "question": f"Write a simple example using {skill_name}",
                "starter_code": "// Your code here",
                "expected_output": "Basic functionality",
                "hint": "Start with the simplest example"
            }
        
        elif level_type == "practice":
            return {
                "type": "project",
                "question": f"Build a mini project with {skill_name}",
                "requirements": [
                    f"Use {skill_name} correctly",
                    "Make it functional",
                    "Add basic styling"
                ],
                "submission_type": "codepen_link"
            }
        
        elif level_type == "challenge":
            return {
                "type": "quiz",
                "questions": [
                    {
                        "question": f"Question about {skill_name}",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A"
                    }
                ],
                "passing_score": 80
            }
        
        else:  # boss
            return {
                "type": "boss_project",
                "question": f"Build a complete project showcasing {skill_name}",
                "requirements": [
                    "Demonstrate mastery",
                    "Include all sub-concepts",
                    "Professional quality",
                    "Deploy live"
                ],
                "submission_type": "github_repo",
                "review_required": True
            }
    
    def _generate_milestones(self, levels: List[Dict], career_goal: str) -> List[Dict]:
        """Generate milestone badges every 5 levels"""
        milestones = []
        
        milestone_names = [
            f"{career_goal} Beginner 🌱",
            f"{career_goal} Apprentice 🎓",
            f"{career_goal} Practitioner 💼",
            f"{career_goal} Expert 🏆",
            f"{career_goal} Master 👑"
        ]
        
        for i in range(0, len(levels), 5):
            if i // 5 < len(milestone_names):
                milestones.append({
                    "level": i + 5,
                    "title": milestone_names[i // 5],
                    "badge": ["🌟", "⭐", "💫", "✨", "🌠"][i // 5 % 5],
                    "description": f"Reached level {i + 5}!"
                })
        
        return milestones
    
    def _calculate_days(self, levels: List[Dict]) -> int:
        """Estimate completion time in days (assuming 1 hour/day)"""
        total_minutes = sum(level["estimated_minutes"] for level in levels)
        return (total_minutes // 60) + 1


# Example usage function
def generate_level_roadmap(original_skills: List[Dict], career_goal: str, learning_level: str) -> Dict:
    """
    Main function to convert skills to levels
    
    Usage:
        skills = [
            {"name": "HTML Basics", "stage": "Beginner", "hours": 10},
            {"name": "CSS Fundamentals", "stage": "Beginner", "hours": 15}
        ]
        
        roadmap = generate_level_roadmap(skills, "Web Developer", "Beginner")
    """
    generator = LevelGenerator()
    return generator.convert_skills_to_levels(original_skills, career_goal, learning_level)


# Testing
if __name__ == "__main__":
    # Sample input
    sample_skills = [
        {"name": "HTML Basics", "stage": "Beginner", "hours": 10},
        {"name": "CSS Fundamentals", "stage": "Beginner", "hours": 15},
        {"name": "JavaScript Basics", "stage": "Beginner", "hours": 20}
    ]
    
    # Generate levels
    result = generate_level_roadmap(sample_skills, "Web Developer", "Beginner")
    
    # Print result
    print(json.dumps(result, indent=2))
    print(f"\n✅ Generated {len(result['levels'])} levels!")