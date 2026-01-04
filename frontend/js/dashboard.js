// Check authentication
if (!api.getToken()) {
    window.location.href = 'index.html';
}

// State
let currentRoadmap = null;
let dashboardData = null;

// DOM Elements
const userName = document.getElementById('userName');
const userCareer = document.getElementById('userCareer');
const completedCount = document.getElementById('completedCount');
const totalCount = document.getElementById('totalCount');
const inProgressCount = document.getElementById('inProgressCount');
const remainingCount = document.getElementById('remainingCount');
const progressPercentage = document.getElementById('progressPercentage');
const progressFill = document.getElementById('progressFill');
const skillsContainer = document.getElementById('skillsContainer');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const logoutBtn = document.getElementById('logoutBtn');
const newRoadmapBtn = document.getElementById('newRoadmapBtn');
const createFirstRoadmap = document.getElementById('createFirstRoadmap');

// Status icons
const statusIcons = {
    'NOT_STARTED': '⚪',
    'IN_PROGRESS': '🔵',
    'COMPLETED': '✅'
};

// Initialize dashboard
async function init() {
    try {
        // Show loading
        loadingState.style.display = 'block';
        if (emptyState) emptyState.style.display = 'none';
        
        // Load dashboard data
        dashboardData = await api.getDashboard();
        
        if (dashboardData.roadmaps.length === 0) {
            showEmptyState();
            return;
        }

        // Use first roadmap (or could allow user to select)
        currentRoadmap = dashboardData.roadmaps[0];
        
        renderDashboard();
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        loadingState.style.display = 'none';
        alert('Failed to load dashboard. Please try again.');
    }
}

// Render dashboard
function renderDashboard() {
    loadingState.style.display = 'none';
    
    // User info
    userName.textContent = `Hello, ${dashboardData.user.username}! 👋`;
    userCareer.textContent = `${currentRoadmap.career_goal} - ${currentRoadmap.learning_level}`;
    
    // Progress stats
    const total = currentRoadmap.skills.length;
    const completed = currentRoadmap.skills.filter(s => s.status === 'COMPLETED').length;
    const inProgress = currentRoadmap.skills.filter(s => s.status === 'IN_PROGRESS').length;
    const remaining = total - completed - inProgress;
    
    if (completedCount) completedCount.textContent = completed;
    if (totalCount) totalCount.textContent = total;
    if (inProgressCount) inProgressCount.textContent = inProgress;
    if (remainingCount) remainingCount.textContent = remaining;
    
    // Progress percentage
    const progress = currentRoadmap.progress_percentage;
    progressPercentage.textContent = `${Math.round(progress)}%`;
    
    // Update progress bar
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
    }
    
    // Render skills
    renderSkills(currentRoadmap.skills);
}

// Render skills list
ffunction renderSkills(skills) {
    const container = document.getElementById('skillsContainer');

    container.className = 'learning-timeline space-y-4';

    container.innerHTML = skills.map((skill, index) => {
        const isCompleted = skill.status === 'COMPLETED';
        const isActive = skill.status === 'IN_PROGRESS';
        const isLocked = skill.status === 'NOT_STARTED' && index > 0 && skills[index - 1].status !== 'COMPLETED';

        return `
            <div class="level-card
                ${isCompleted ? 'completed' : ''}
                ${isActive ? 'active' : ''}
                ${isLocked ? 'locked' : ''}"
                data-skill-id="${skill.id}"
            >

                <div class="level-header">
                    <div>
                        <div class="level-index">
                            LEVEL ${String(index + 1).padStart(2, '0')}
                        </div>

                        <div class="level-title">
                            ${skill.skill_name}
                        </div>

                        <div class="level-meta">
                            ${skill.estimated_hours ? `Estimated time: ${skill.estimated_hours} hours` : ''}
                        </div>
                    </div>

                    <div class="status-badge
                        ${isCompleted ? 'status-completed' : isActive ? 'status-active' : 'status-locked'}">
                        ${isCompleted ? 'Completed' : isActive ? 'Active' : 'Locked'}
                    </div>
                </div>

                ${skill.why_important ? `
                    <p class="mt-3 text-sm text-slate-600 leading-relaxed">
                        ${skill.why_important}
                    </p>
                ` : ''}

                <div class="flex gap-2 mt-4">
                    <button class="status-btn ${skill.status === 'NOT_STARTED' ? 'active' : ''}"
                        data-status="NOT_STARTED"
                        data-status-id="${skill.status_id}">
                        Not started
                    </button>

                    <button class="status-btn ${skill.status === 'IN_PROGRESS' ? 'active' : ''}"
                        data-status="IN_PROGRESS"
                        data-status-id="${skill.status_id}">
                        In progress
                    </button>

                    <button class="status-btn ${skill.status === 'COMPLETED' ? 'active' : ''}"
                        data-status="COMPLETED"
                        data-status-id="${skill.status_id}">
                        Completed
                    </button>
                </div>
            </div>
        `;
    }).join('');

    document.querySelectorAll('.status-btn').forEach(btn => {
        btn.addEventListener('click', handleStatusChange);
    });
}

// Handle status change
async function handleStatusChange(e) {
    const btn = e.currentTarget;
    const statusId = parseInt(btn.dataset.statusId);
    const newStatus = btn.dataset.status;
    
    // Get all buttons in this skill card
    const skillCard = btn.closest('.skill-card');
    const allButtons = skillCard.querySelectorAll('.status-btn');
    
    try {
        // Optimistic UI update
        allButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        if (newStatus === 'COMPLETED') {
            skillCard.classList.add('completed');
        } else {
            skillCard.classList.remove('completed');
        }
        
        // Update backend
        await api.updateSkillStatus(statusId, newStatus);
        
        // Reload dashboard to update stats
        dashboardData = await api.getDashboard();
        currentRoadmap = dashboardData.roadmaps[0];
        
        // Update progress display
        const total = currentRoadmap.skills.length;
        const completed = currentRoadmap.skills.filter(s => s.status === 'COMPLETED').length;
        const inProgress = currentRoadmap.skills.filter(s => s.status === 'IN_PROGRESS').length;
        const remaining = total - completed - inProgress;
        
        if (completedCount) completedCount.textContent = completed;
        if (inProgressCount) inProgressCount.textContent = inProgress;
        if (remainingCount) remainingCount.textContent = remaining;
        
        const progress = currentRoadmap.progress_percentage;
        progressPercentage.textContent = `${Math.round(progress)}%`;
        
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        
    } catch (error) {
        console.error('Failed to update status:', error);
        alert('Failed to update skill status. Please try again.');
        
        // Revert UI
        init();
    }
}

// Show empty state
function showEmptyState() {
    loadingState.style.display = 'none';
    if (emptyState) {
        emptyState.style.display = 'block';
    }
    
    const progressSection = document.querySelector('.progress-hero');
    const roadmapSection = document.querySelector('#skillsContainer').parentElement;
    
    if (progressSection) progressSection.style.display = 'none';
    if (roadmapSection) roadmapSection.style.display = 'none';
}

// Logout
logoutBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to logout?')) {
        api.removeToken();
        localStorage.removeItem('user');
        window.location.href = 'index.html';
    }
});

// New roadmap
if (newRoadmapBtn) {
    newRoadmapBtn.addEventListener('click', () => {
        window.location.href = 'setup.html';
    });
}

if (createFirstRoadmap) {
    createFirstRoadmap.addEventListener('click', () => {
        window.location.href = 'setup.html';
    });
}

// Initialize
init();
