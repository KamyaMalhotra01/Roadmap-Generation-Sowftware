import requests
from typing import Optional
from config import GROQ_API_KEY, GROQ_MODEL

class AIService:
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate_skill_explanation(
        self, 
        skill_name: str, 
        career_goal: str, 
        learning_stage: str
    ) -> str:
        """Generate AI explanation for why a skill is important"""
        
        prompt = f"""You are a career mentor. Explain in 2-3 sentences why "{skill_name}" is important for someone learning to become a {career_goal}. 
        
Learning Stage: {learning_stage}

Keep it motivating, practical, and beginner-friendly. Focus on real-world applications."""

        try:
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",#proves who you are
                #bearer{self.api_key} is the token(from groq) that proves your identity
                "Content-Type": "application/json"#type of data being sent
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful career mentor who explains technical concepts clearly."#sets AI personality/behavior
                    },
                    {
                        "role": "user",
                        "content": prompt #user's input/question(prompt)
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 150
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                explanation = result["choices"][0]["message"]["content"].strip()
                return explanation
            else:
                print(f"Groq API error: {response.status_code}")
                return self._get_fallback_explanation(skill_name, career_goal)
                
        except Exception as e:
            print(f" AI generation failed: {str(e)}")
            return self._get_fallback_explanation(skill_name, career_goal)
    
    def _get_fallback_explanation(self, skill_name: str, career_goal: str) -> str:
        """Fallback explanation if AI fails"""
        return f"{skill_name} is a fundamental skill for {career_goal} that will help you build professional projects and advance your career."
    
    def generate_batch_explanations(self, skills: list, career_goal: str) -> dict:
        """Generate explanations for multiple skills"""
        explanations = {}
        
        for skill in skills:
            skill_name = skill["name"]
            learning_stage = skill["stage"]
            
            explanation = self.generate_skill_explanation(
                skill_name, 
                career_goal, 
                learning_stage
            )
            
            explanations[skill_name] = explanation
        
        return explanations

# Global AI service instance
ai_service = AIService()