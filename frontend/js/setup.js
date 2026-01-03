// Check authentication
if (!api.getToken()) {
    window.location.href = 'index.html';
}

// State
let selectedCareer = null;
let selectedLevel = null;
let existingSkills = [];

// DOM Elements
const careerGoalsContainer = document.getElementById('careerGoalsContainer');
const skillInput = document.getElementById('skillInput');
const addSkillBtn = document.getElementById('addSkillBtn');
const skillsContainer = document.getElementById('skillsContainer');
const setupForm = document.getElementById('setupForm');
const loadingMessage = document.getElementById('loadingMessage');

// Career goal icons
const careerIcons = {
    'Web Developer': '💻',
    'Data Analyst': '📊',
    'App Developer': '📱',
};

// Initialize
async function init() {
    try {
        const data = await api.getCareerGoals();
        renderCareerGoals(data.career_goals);
        setupEventListeners();
    } catch (error) {
        console.error('Failed to load career goals:', error);
        alert('Failed to load career goals. Please try again.');
    }
}

// Render career goal options
function renderCareerGoals(goals) {
    careerGoalsContainer.innerHTML = goals.map(goal => `
        <div class="option-card" data-career="${goal}">
            <div class="option-icon">${careerIcons[goal] || '🎯'}</div>
            <div class="option-title">${goal}</div>
        </div>
    `).join('');

    // Add click handlers
    document.querySelectorAll('[data-career]').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('[data-career]').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedCareer = card.dataset.career;
        });
    });
}

// Setup event listeners
function setupEventListeners() {
    // Learning level selection
    document.querySelectorAll('[data-level]').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('[data-level]').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedLevel = card.dataset.level;
        });
    });

    // Add skill
    addSkillBtn.addEventListener('click', addSkill);
    skillInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addSkill();
        }
    });

    // Form submission
    setupForm.addEventListener('submit', handleSubmit);
}

// Add skill to list
function addSkill() {
    const skill = skillInput.value.trim();
    
    if (!skill) return;
    
    if (existingSkills.includes(skill)) {
        alert('Skill already added!');
        return;
    }
    
    existingSkills.push(skill);
    renderSkills();
    skillInput.value = '';
}

// Remove skill
function removeSkill(skill) {
    existingSkills = existingSkills.filter(s => s !== skill);
    renderSkills();
}

// Render skills tags
function renderSkills() {
    if (existingSkills.length === 0) {
        skillsContainer.innerHTML = '<p style="color: rgba(255,255,255,0.6); font-size: 14px;">No skills added yet</p>';
        return;
    }

    skillsContainer.innerHTML = existingSkills.map(skill => `
        <div class="skill-tag">
            <span>${skill}</span>
            <span class="remove-skill" onclick="removeSkill('${skill}')">×</span>
        </div>
    `).join('');
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();

    // Validation
    if (!selectedCareer) {
        alert('Please select a career goal');
        return;
    }

    if (!selectedLevel) {
        alert('Please select your learning level');
        return;
    }

    try {
        // Show loading
        setupForm.style.display = 'none';
        loadingMessage.style.display = 'block';

        // Create roadmap
        const roadmap = await api.createRoadmap(
            selectedCareer,
            selectedLevel,
            existingSkills
        );

        console.log('Roadmap created:', roadmap);

        // Redirect to dashboard
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1500);

    } catch (error) {
        console.error('Failed to create roadmap:', error);
        alert('Failed to create roadmap: ' + error.message);
        setupForm.style.display = 'block';
        loadingMessage.style.display = 'none';
    }
}

// Make removeSkill globally accessible
window.removeSkill = removeSkill;

// Initialize on load
init();
