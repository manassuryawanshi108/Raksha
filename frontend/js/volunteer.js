/**
 * Volunteer Page JavaScript
 * Changes 4 & 5a: self-assignment, task decline modal, removed register form & match recommendations
 */

let allVolunteers = [];
let allTasks = [];

// Current authenticated user — set after DOMContentLoaded
let currentUser = null;

/**
 * Mobile menu toggle
 */
function toggleMenu() {
    document.getElementById('navbarNav').classList.toggle('active');
}

/**
 * Show alert message
 */
function showAlert(message, type = 'success') {
    const container = document.getElementById('alertContainer');
    container.innerHTML = `<div class="alert alert-${type}">${escapeHtml(message)}</div>`;
    setTimeout(() => container.innerHTML = '', 5000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── Volunteers List ───────────────────────────────────────────────────────────

/**
 * Load all volunteers
 */
async function loadVolunteers() {
    const tbody = document.getElementById('volunteersTableBody');
    tbody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner"></div>Loading volunteers...</td></tr>';

    try {
        const response = await API.getVolunteers();

        if (response.success) {
            allVolunteers = response.volunteers;
            renderVolunteers(allVolunteers);
            updateVolunteerStats();
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Failed to load volunteers</td></tr>';
        }
    } catch (error) {
        console.error('Error loading volunteers:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Error loading volunteers. Is the backend running?</td></tr>';
        loadDemoVolunteers();
    }
}

/**
 * Load demo volunteers when backend unavailable
 */
function loadDemoVolunteers() {
    allVolunteers = [
        { id: 'v1', name: 'Rajesh Kumar', skills: ['plumbing', 'water treatment', 'construction'], latitude: 28.6139, longitude: 77.2090, phone: '+91-9876543210', email: 'rajesh@volunteer.org', status: 'available' },
        { id: 'v2', name: 'Priya Sharma',  skills: ['medical', 'nursing', 'first aid'],            latitude: 28.5355, longitude: 77.3910, phone: '+91-9876543211', email: 'priya@volunteer.org',  status: 'available' },
        { id: 'v3', name: 'Mohammed Ali',  skills: ['cooking', 'food distribution', 'logistics'],  latitude: 19.0760, longitude: 72.8777, phone: '+91-9876543212', email: 'ali@volunteer.org',   status: 'assigned' },
        { id: 'v4', name: 'Sunita Devi',   skills: ['teaching', 'education', 'childcare'],         latitude: 18.9388, longitude: 72.8354, phone: '+91-9876543213', email: 'sunita@volunteer.org', status: 'available' }
    ];
    renderVolunteers(allVolunteers);
    updateVolunteerStats();
}

/**
 * Render volunteers to table
 */
function renderVolunteers(volunteers) {
    const tbody = document.getElementById('volunteersTableBody');

    if (volunteers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No volunteers found</td></tr>';
        return;
    }

    tbody.innerHTML = volunteers.map(vol => `
        <tr>
            <td><strong>${escapeHtml(vol.name)}</strong></td>
            <td>${vol.skills?.map(s => `<span class="badge badge-pending">${escapeHtml(s)}</span>`).join(' ') || '—'}</td>
            <td>${vol.latitude?.toFixed(2)}, ${vol.longitude?.toFixed(2)}</td>
            <td>${escapeHtml(vol.phone || '—')}<br>${escapeHtml(vol.email || '')}</td>
            <td>
                <span class="badge ${vol.status === 'available' ? 'badge-success' : 'badge-assigned'}">
                    ${escapeHtml(vol.status)}
                </span>
            </td>
            <td>
                ${vol.status === 'available'
                    ? `<button class="btn btn-outline btn-sm" onclick="viewVolunteerTasks('${vol.id}')">View Tasks</button>`
                    : '<span class="text-muted">On assignment</span>'}
            </td>
        </tr>
    `).join('');
}

/**
 * Update volunteer statistics
 */
async function updateVolunteerStats() {
    try {
        const [volunteersResponse, availableResponse] = await Promise.all([
            API.getVolunteers(),
            API.getAvailableVolunteers()
        ]);

        if (volunteersResponse.success) {
            document.getElementById('totalVolunteers').textContent = volunteersResponse.count || 0;
        }
        if (availableResponse.success) {
            document.getElementById('availableVolunteers').textContent = availableResponse.count || 0;
        }

        const total     = parseInt(document.getElementById('totalVolunteers').textContent) || 0;
        const available = parseInt(document.getElementById('availableVolunteers').textContent) || 0;
        document.getElementById('assignedTasks').textContent = total - available;
        document.getElementById('completedTasks').textContent = '0';
    } catch (error) {
        document.getElementById('totalVolunteers').textContent = allVolunteers.length;
        document.getElementById('availableVolunteers').textContent = allVolunteers.filter(v => v.status === 'available').length;
        document.getElementById('assignedTasks').textContent = allVolunteers.filter(v => v.status === 'assigned').length;
        document.getElementById('completedTasks').textContent = '0';
    }
}

/**
 * View tasks for a volunteer (quick alert summary)
 */
async function viewVolunteerTasks(volunteerId) {
    try {
        const response = await API.getVolunteerTasks(volunteerId);

        if (response.success) {
            if (response.tasks.length === 0) {
                showAlert('No tasks assigned to this volunteer', 'warning');
            } else {
                const taskList = response.tasks.map(t =>
                    `- ${t.issue_location || t.issue_id} (${t.status})`
                ).join('\n');
                alert(`Tasks for volunteer:\n\n${taskList}`);
            }
        }
    } catch (error) {
        showAlert('Error loading tasks: ' + error.message, 'error');
    }
}

// ── Change 4a: Available Tasks (self-assignment for approved volunteers) ──────

/**
 * Load all pending issues as "available tasks" for volunteers.
 * The section is shown only when the current user is an approved volunteer.
 */
async function loadAvailableTasks() {
    const section  = document.getElementById('availableTasksSection');
    const tbody    = document.getElementById('availableTasksBody');
    if (!section || !tbody) return;

    // Only volunteers see this section
    if (!currentUser || currentUser.role !== 'volunteer' || currentUser.status !== 'approved') {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    tbody.innerHTML = '<tr><td colspan="5" class="text-center"><div class="spinner"></div>Loading available tasks...</td></tr>';

    try {
        const res = await API.getIssues();
        const issues = (res.issues || []).filter(i => i.status === 'pending');

        if (!issues.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No pending tasks available right now.</td></tr>';
            return;
        }

        tbody.innerHTML = issues.map(iss => `
            <tr id="avail-row-${iss.id}">
                <td><strong>${escapeHtml(iss.location)}</strong></td>
                <td>${escapeHtml(iss.issue)}</td>
                <td><span class="badge badge-pending">${escapeHtml(iss.category)}</span></td>
                <td><span class="badge ${API.getPriorityBadgeClass(iss.priority)}">${escapeHtml(iss.priority)}</span></td>
                <td>
                    <button id="self-assign-btn-${iss.id}"
                            class="btn btn-primary btn-sm"
                            onclick="selfAssignTask('${iss.id}', this)">
                        Volunteer for this task
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Could not load tasks: ${escapeHtml(err.message)}</td></tr>`;
    }
}

/**
 * Self-assign the current volunteer to a pending issue (Change 4a).
 */
async function selfAssignTask(issueId, btn) {
    if (!currentUser || !currentUser.id) {
        showAlert('Cannot determine your user ID. Please log in again.', 'error');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Assigning…';

    try {
        await API.assignTask(issueId, currentUser.id);
        showAlert('You have been assigned to this task! Check your Assigned Tasks below.', 'success');
        // Remove the row from the available list
        const row = document.getElementById('avail-row-' + issueId);
        if (row) row.remove();
        // Refresh assigned tasks
        loadTasks();
    } catch (err) {
        showAlert('Failed to self-assign: ' + err.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Volunteer for this task';
    }
}

// ── Change 4c: Decline Modal ──────────────────────────────────────────────────

let _declineTaskId = null;

/**
 * Open the decline confirmation modal.
 */
function openDeclineModal(taskId) {
    _declineTaskId = taskId;
    document.getElementById('declineReasonInput').value = '';
    document.getElementById('declineModal').classList.remove('hidden');
}

/**
 * Close the decline modal without action.
 */
function closeDeclineModal() {
    _declineTaskId = null;
    document.getElementById('declineModal').classList.add('hidden');
}

/**
 * Confirm and submit the task decline.
 */
async function confirmDecline() {
    if (!_declineTaskId) return;

    const reason  = document.getElementById('declineReasonInput').value.trim();
    const token   = window.RakshaAuth ? window.RakshaAuth.getToken() : null;
    const confirmBtn = document.getElementById('confirmDeclineBtn');

    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Declining…';

    try {
        await API.declineTask(_declineTaskId, reason, token);
        closeDeclineModal();
        showAlert('Task declined successfully.', 'success');
        loadTasks();
    } catch (err) {
        showAlert('Failed to decline task: ' + err.message, 'error');
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Confirm Decline';
    }
}

// ── Change 4: Assigned Tasks ──────────────────────────────────────────────────

/**
 * Load assigned tasks.
 * For volunteers: shows their own tasks (with Decline button).
 * For NGO/admin: shows a full task roster (no Decline button).
 */
async function loadTasks() {
    const tbody = document.getElementById('tasksTableBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner"></div>Loading tasks...</td></tr>';

    const isVolunteer = currentUser && currentUser.role === 'volunteer';
    const token       = window.RakshaAuth ? window.RakshaAuth.getToken() : null;

    try {
        let tasks = [];

        if (isVolunteer && currentUser.id) {
            // Volunteer sees only their own tasks
            const res = await API.getVolunteerTasks(currentUser.id);
            tasks = res.tasks || [];
        } else {
            // NGO/admin — use the general volunteer tasks endpoint (no admin restriction)
            const res = await API.getAllTasks(token);
            tasks = res.tasks || [];
        }

        if (!tasks.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No assigned tasks.</td></tr>';
            return;
        }

        tbody.innerHTML = tasks.map(t => {
            const declineBtn = isVolunteer && t.status === 'assigned'
                ? `<button class="btn btn-danger btn-sm" id="decline-btn-${t.id}" onclick="openDeclineModal('${t.id}')">Decline</button>`
                : '';
            return `
                <tr>
                    <td>${escapeHtml(t.issue_location || t.issue_id || '—')}</td>
                    <td>${escapeHtml(t.location || '—')}</td>
                    <td>${escapeHtml(t.volunteer_name || t.volunteer_id || '—')}</td>
                    <td>${escapeHtml(t.category || '—')}</td>
                    <td><span class="badge ${API.getStatusBadgeClass(t.status)}">${escapeHtml(t.status)}</span></td>
                    <td>${declineBtn}</td>
                </tr>`;
        }).join('');
    } catch (error) {
        console.error('Error loading tasks:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Could not load tasks. Is the backend running?</td></tr>';
    }
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    // Run auth guard first, then read the verified user
    if (window.initAuthGuard) {
        await initAuthGuard();
    }
    currentUser = window.RakshaAuth ? window.RakshaAuth.getUser() : null;

    loadVolunteers();
    loadAvailableTasks();
    loadTasks();
});
