// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// API Client Class
class APIClient {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    // Get auth token from localStorage
    getToken() {
        return localStorage.getItem('token');
    }

    // Set auth token
    setToken(token) {
        localStorage.setItem('token', token);
    }

    // Remove auth token
    removeToken() {
        localStorage.removeItem('token');
    }

    // Get current user data
    getCurrentUser() {
        return JSON.parse(localStorage.getItem('user') || '{}');
    }

    // Set current user data
    setCurrentUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const token = this.getToken();

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (token && !options.skipAuth) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                console.error('Failed to parse JSON response:', response.status, response.statusText);
                throw new Error(`Invalid response format: ${response.status} ${response.statusText}`);
            }

            if (!response.ok) {
                throw new Error(data.detail || data.message || `Request failed: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Error:', error.message);
            throw error;
        }
    }

    // ============ AUTH ENDPOINTS ============

    async register(username, password, email = null) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, password, email }),
            skipAuth: true,
        });
    }

    async login(username, password) {
        // FastAPI OAuth2 expects form data
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        // Store token
        this.setToken(data.access_token);

        // Fetch and store user info
        const user = await this.getMe();
        this.setCurrentUser(user);

        return data;
    }

    async getMe() {
        return this.request('/auth/me');
    }

    // ============ CAREER GOALS ============

    async getCareerGoals() {
        return this.request('/career-goals', { skipAuth: true });
    }

    // ============ ROADMAP ENDPOINTS ============

    async createRoadmap(careerGoal, learningLevel, existingSkills = []) {
        return this.request('/roadmaps/create', {
            method: 'POST',
            body: JSON.stringify({
                career_goal: careerGoal,
                learning_level: learningLevel,
                existing_skills: existingSkills,
            }),
        });
    }

    async getMyRoadmaps() {
        return this.request('/roadmaps/my-roadmaps');
    }

    // ============ SKILL STATUS ============

    async updateSkillStatus(statusId, status) {
        return this.request(`/skills/${statusId}/update`, {
            method: 'PATCH',
            body: JSON.stringify({ status }),
        });
    }

    // ============ DASHBOARD ============

    async getDashboard() {
        return this.request('/dashboard');
    }
}

// Export global API instance
const api = new APIClient();
