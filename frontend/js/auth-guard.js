/**
 * Raksha Auth Guard
 * Include this script on every protected page BEFORE other scripts.
 * Redirects unauthenticated users to login.html.
 */

const AUTH_API = 'http://localhost:8000';
const AUTH_KEY = 'raksha_token';
const USER_KEY = 'raksha_user';

// Pages that don't require auth
const PUBLIC_PAGES = ['login.html', 'pending.html'];

function isPublicPage() {
    const path = window.location.pathname;
    return PUBLIC_PAGES.some(p => path.endsWith(p));
}

function getToken() {
    return localStorage.getItem(AUTH_KEY);
}

function getUser() {
    try {
        return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
    } catch { return null; }
}

function logout() {
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(USER_KEY);
    window.location.href = 'login.html';
}

/**
 * Verify token with backend and get fresh user data
 */
async function verifySession() {
    const token = getToken();
    if (!token) return null;

    try {
        const res = await fetch(`${AUTH_API}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!res.ok) return null;
        const data = await res.json();
        if (data.success && data.user) {
            localStorage.setItem(USER_KEY, JSON.stringify(data.user));
            return data.user;
        }
        return null;
    } catch {
        // Backend might be down — trust local cache briefly
        return getUser();
    }
}

/**
 * Check if user has required role access
 */
function hasAccess(user, requiredRoles) {
    if (!user) return false;
    if (!requiredRoles || requiredRoles.length === 0) return true;
    // Admin always has access
    if (user.role === 'admin') return true;
    // Check if user's role is in required list
    if (!requiredRoles.includes(user.role)) return false;
    // Volunteers must be approved
    if (user.role === 'volunteer' && user.status !== 'approved') return false;
    return true;
}

/**
 * Update the navbar to show logged-in user info
 */
function renderAuthNav(user) {
    const navAuth = document.getElementById('navAuth');
    if (!navAuth) return;

    if (user) {
        const roleBadge = user.role === 'admin' ? '🛡️' : user.role === 'ngo' ? '🏢' : '🤝';
        navAuth.innerHTML = `
            <span style="color: var(--text-secondary); font-size: 0.85rem;">
                ${roleBadge} ${user.display_name || user.email}
            </span>
            <button class="btn btn-secondary btn-sm" onclick="logout()">Log out</button>
        `;

        // Show admin link if admin
        if (user.role === 'admin') {
            const nav = document.getElementById('navbarNav');
            if (nav && !nav.querySelector('[href="admin.html"]')) {
                const li = document.createElement('li');
                li.innerHTML = '<a href="admin.html">Admin</a>';
                nav.appendChild(li);
            }
        }
    } else {
        navAuth.innerHTML = `
            <a href="login.html" class="btn btn-secondary btn-sm">Log in</a>
            <a href="login.html#register" class="btn btn-primary btn-sm">Sign up</a>
        `;
    }
}

/**
 * Authorized fetch — attaches token to API requests
 */
async function authFetch(url, opts = {}) {
    const token = getToken();
    if (!token) { logout(); return null; }

    opts.headers = {
        ...opts.headers,
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
    };

    const res = await fetch(url, opts);
    if (res.status === 401 || res.status === 403) {
        logout();
        return null;
    }
    return res.json();
}

/**
 * Main auth gate — runs on page load
 */
async function initAuthGuard(requiredRoles = []) {
    if (isPublicPage()) return;

    const token = getToken();
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const user = await verifySession();

    if (!user) {
        logout();
        return;
    }

    // Check role-based access
    if (!hasAccess(user, requiredRoles)) {
        if (user.role === 'volunteer' && user.status === 'pending') {
            window.location.href = 'pending.html';
        } else {
            // Show access denied
            document.body.innerHTML = `
                <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;background:#0a0e1a;color:#f1f5f9;font-family:Inter,sans-serif;text-align:center;">
                    <div>
                        <h1 style="font-size:3rem;margin-bottom:1rem;">🚫</h1>
                        <h2>Access Denied</h2>
                        <p style="color:#94a3b8;margin:1rem 0;">You don't have permission to view this page.</p>
                        <a href="index.html" style="color:#6366f1;">← Back to Home</a>
                    </div>
                </div>
            `;
        }
        return;
    }

    // Render user info in navbar
    renderAuthNav(user);
}

// Export globally
window.RakshaAuth = {
    getToken, getUser, logout, verifySession,
    hasAccess, authFetch, initAuthGuard, renderAuthNav,
    AUTH_API
};
