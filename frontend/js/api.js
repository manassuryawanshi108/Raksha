/**
 * API Client for NGO Resource Allocation System
 * Centralized fetch wrappers for backend communication
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling and auth token injection
 */
async function fetchAPI(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = localStorage.getItem('raksha_token');

    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        }
    };

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            const errorMsg = data.detail || data.message || `Request failed (${response.status})`;
            throw new Error(errorMsg);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ==================== Issues API ====================

/**
 * Get all issues with optional filters
 */
async function getIssues(filters = {}) {
    const params = new URLSearchParams(filters);
    return fetchAPI(`/issues/list?${params}`);
}

/**
 * Get a single issue by ID
 */
async function getIssue(issueId) {
    return fetchAPI(`/issues/${issueId}`);
}

/**
 * Get issues formatted for map markers
 */
async function getMapMarkers() {
    return fetchAPI('/issues/map/markers');
}

/**
 * Get issues summary statistics
 */
async function getIssuesSummary() {
    return fetchAPI('/issues/stats/summary');
}

// ==================== Upload API ====================

/**
 * Upload a single issue via form data
 */
async function uploadIssue(formData) {
    const url = `${API_BASE_URL}/upload/form`;

    const form = new FormData();
    form.append('location', formData.location);
    form.append('issue', formData.issue);
    form.append('people_count', formData.people_count);
    form.append('latitude', formData.latitude);
    form.append('longitude', formData.longitude);
    if (formData.contact_info) {
        form.append('contact_info', formData.contact_info);
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: form
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Upload failed');
        }

        return data;
    } catch (error) {
        console.error('Upload Error:', error);
        throw error;
    }
}

/**
 * Upload multiple issues via CSV file
 */
async function uploadCSV(file) {
    const url = `${API_BASE_URL}/upload/csv`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'CSV upload failed');
        }

        return data;
    } catch (error) {
        console.error('CSV Upload Error:', error);
        throw error;
    }
}

// ==================== AI Processing API ====================

/**
 * Classify an issue text
 */
async function classifyIssue(text, peopleCount = 100) {
    const params = new URLSearchParams({ text, people_count: peopleCount.toString() });
    return fetchAPI(`/ai/classify?${params}`);
}

/**
 * Get AI statistics
 */
async function getAIStats() {
    return fetchAPI('/ai/stats');
}

// ==================== Volunteer API ====================

/**
 * Register a new volunteer
 */
async function registerVolunteer(volunteerData) {
    return fetchAPI('/volunteer/register', {
        method: 'POST',
        body: JSON.stringify(volunteerData)
    });
}

/**
 * Get all volunteers
 */
async function getVolunteers() {
    return fetchAPI('/volunteer/list');
}

/**
 * Get available volunteers
 */
async function getAvailableVolunteers() {
    return fetchAPI('/volunteer/available');
}

/**
 * Get best volunteer match for an issue
 */
async function getVolunteerMatch(issueId) {
    return fetchAPI(`/volunteer/match/${issueId}`);
}

/**
 * Get matches for all pending issues
 */
async function getAllMatches() {
    return fetchAPI('/volunteer/match-all');
}

/**
 * Assign a task to a volunteer
 */
async function assignTask(issueId, volunteerId) {
    const params = new URLSearchParams({ issue_id: issueId, volunteer_id: volunteerId });
    return fetchAPI(`/volunteer/assign?${params}`, { method: 'POST' });
}

/**
 * Get tasks assigned to a volunteer
 */
async function getVolunteerTasks(volunteerId) {
    return fetchAPI(`/volunteer/tasks/${volunteerId}`);
}

/**
 * Mark a task as completed
 */
async function completeTask(taskId) {
    return fetchAPI(`/volunteer/task/${taskId}/complete`, { method: 'PUT' });
}

// ==================== Admin API ====================

/** Get all tasks (admin/engineer) */
async function adminListTasks(token) {
    return fetchAPI('/admin/tasks', { headers: { Authorization: 'Bearer ' + token } });
}

/** Assign task via admin endpoint */
async function adminAssignTask(issueId, volunteerId, token) {
    const params = new URLSearchParams({ issue_id: issueId, volunteer_id: volunteerId });
    return fetchAPI(`/admin/assign-task?${params}`, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token }
    });
}

/** Volunteer declines a task */
async function declineTask(taskId, reason, token) {
    const params = new URLSearchParams({ reason });
    return fetchAPI(`/admin/tasks/${taskId}/decline?${params}`, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token }
    });
}

/** Get ALL tasks — accessible to any authenticated user (NGO/admin/volunteer) */
async function getAllTasks(token) {
    const headers = token ? { Authorization: 'Bearer ' + token } : {};
    return fetchAPI('/volunteer/tasks/all', { headers });
}

/** Admin verifies volunteer documents */
async function adminVerifyDocuments(userId, verified, notes, token) {
    const params = new URLSearchParams({ verified, notes });
    return fetchAPI(`/admin/verify-documents/${userId}?${params}`, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token }
    });
}

/** Get pending volunteers (admin) */
async function adminGetPending(token) {
    return fetchAPI('/admin/pending-volunteers', { headers: { Authorization: 'Bearer ' + token } });
}

/** Approve volunteer */
async function adminApprove(userId, token) {
    return fetchAPI(`/admin/approve/${userId}`, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token }
    });
}

/** Reject volunteer */
async function adminReject(userId, token) {
    return fetchAPI(`/admin/reject/${userId}`, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token }
    });
}

/** NGO assigns an issue to an approved volunteer */
async function ngoAssignTask(issueId, volunteerId, token) {
    const params = new URLSearchParams({ issue_id: issueId, volunteer_id: volunteerId });
    return fetchAPI(`/admin/ngo/assign-task?${params}`, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token }
    });
}

/** NGO adds a new volunteer directly */
async function ngoAddVolunteer(data, token) {
    const params = new URLSearchParams({
        display_name: data.display_name,
        skills: data.skills || '',
        phone: data.phone || '',
        email: data.email || '',
        latitude: data.latitude || 0,
        longitude: data.longitude || 0,
    });
    return fetchAPI(`/admin/ngo/add-volunteer?${params}`, {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token }
    });
}

// ==================== Utility Functions ====================

/**
 * Get urgency badge class
 */
function getUrgencyBadgeClass(urgency) {
    // Normalize: seeded data may be 0-100, API data is 0-1
    const u = urgency > 1 ? urgency / 100 : urgency;
    if (u >= 0.7) return 'badge-high';
    if (u >= 0.4) return 'badge-medium';
    return 'badge-low';
}

/**
 * Get priority badge class
 */
function getPriorityBadgeClass(priority) {
    switch (priority?.toLowerCase()) {
        case 'high': return 'badge-high';
        case 'medium': return 'badge-medium';
        case 'low': return 'badge-low';
        default: return 'badge-pending';
    }
}

/**
 * Get status badge class
 */
function getStatusBadgeClass(status) {
    switch (status?.toLowerCase()) {
        case 'pending': return 'badge-pending';
        case 'assigned': return 'badge-assigned';
        case 'completed': return 'badge-success';
        default: return 'badge-pending';
    }
}

/**
 * Get marker color based on urgency
 */
function getMarkerColor(urgency) {
    if (urgency >= 0.7) return '#ef4444'; // Red
    if (urgency >= 0.4) return '#f59e0b'; // Orange
    return '#10b981'; // Green
}

// Export for use in other files
window.API = {
    // Admin
    adminListTasks,
    adminAssignTask,
    declineTask,
    adminVerifyDocuments,
    adminGetPending,
    adminApprove,
    adminReject,
    // NGO
    ngoAssignTask,
    ngoAddVolunteer,
    // Issues
    getIssues,
    getIssue,
    getMapMarkers,
    getIssuesSummary,
    // Upload
    uploadIssue,
    uploadCSV,
    // AI
    classifyIssue,
    getAIStats,
    // Volunteers
    registerVolunteer,
    getVolunteers,
    getAvailableVolunteers,
    getVolunteerMatch,
    getAllMatches,
    assignTask,
    getVolunteerTasks,
    getAllTasks,
    completeTask,
    // Utilities
    getUrgencyBadgeClass,
    getPriorityBadgeClass,
    getStatusBadgeClass,
    getMarkerColor
};
