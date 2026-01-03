// DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const showRegisterBtn = document.getElementById('showRegister');
const showLoginBtn = document.getElementById('showLogin');
const errorMessage = document.getElementById('errorMessage');

// Check if already logged in
if (api.getToken()) {
    window.location.href = 'dashboard.html';
}

// Toggle between login and register
showRegisterBtn.addEventListener('click', (e) => {
    e.preventDefault();
    loginForm.style.display = 'none';
    registerForm.style.display = 'block';
    hideError();
});

showLoginBtn.addEventListener('click', (e) => {
    e.preventDefault();
    registerForm.style.display = 'none';
    loginForm.style.display = 'block';
    hideError();
});

// Handle Login
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();

    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    if (!username || !password) {
        showError('Please fill in all fields');
        return;
    }

    try {
        // Disable button
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Signing in...</span>';

        await api.login(username, password);

        // Check if user has roadmaps
        const roadmaps = await api.getMyRoadmaps();
        
        if (roadmaps.length === 0) {
            // No roadmaps, go to setup
            window.location.href = 'setup.html';
        } else {
            // Has roadmaps, go to dashboard
            window.location.href = 'dashboard.html';
        }
    } catch (error) {
        showError(error.message || 'Login failed. Please try again.');
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Sign In</span><span class="btn-arrow">→</span>';
    }
});

// Handle Register
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();

    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;

    if (!username || !password) {
        showError('Username and password are required');
        return;
    }

    if (password.length < 6) {
        showError('Password must be at least 6 characters');
        return;
    }

    try {
        // Disable button
        const submitBtn = registerForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Creating account...</span>';

        await api.register(username, password, email || null);
        
        // Auto-login after registration
        await api.login(username, password);
        
        // Go to setup page
        window.location.href = 'setup.html';
    } catch (error) {
        showError(error.message || 'Registration failed. Please try again.');
        const submitBtn = registerForm.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Create Account</span><span class="btn-arrow">→</span>';
    }
});

// Helper functions
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

function hideError() {
    errorMessage.classList.remove('show');
}
