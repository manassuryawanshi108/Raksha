/**
 * Dashboard JavaScript - Issue management and display
 * Changes: Accessibility column, Photo column, volunteer read-only enforcement
 */

let allIssues = [];

/**
 * Mobile menu toggle
 */
function toggleMenu() {
    document.getElementById('navbarNav').classList.toggle('active');
}

/**
 * Load all issues from API
 */
async function loadIssues() {
    const tbody = document.getElementById('issuesTableBody');
    tbody.innerHTML = '<tr><td colspan="10" class="text-center"><div class="spinner"></div>Loading issues...</td></tr>';

    try {
        const response = await API.getIssues();

        if (response.success) {
            allIssues = response.issues;
            applyFilters();
        } else {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center">Failed to load issues</td></tr>';
        }
    } catch (error) {
        console.error('Error loading issues:', error);
        tbody.innerHTML = '<tr><td colspan="10" class="text-center">Error loading issues. Is the backend running?</td></tr>';
        loadDemoData();
    }
}

/**
 * Load demo data when backend is unavailable
 */
function loadDemoData() {
    allIssues = [
        {
            id: '1',
            location: 'Village A, Rural District',
            issue: 'No clean water for 100 people',
            category: 'Water',
            people_count: 100,
            urgency: 0.75,
            priority: 'High',
            status: 'pending',
            assigned_to: null,
            photo_url: null
        },
        {
            id: '2',
            location: 'Refugee Camp Sector 3',
            issue: 'Food shortage - 500 families need rations',
            category: 'Food',
            people_count: 2500,
            urgency: 0.9,
            priority: 'High',
            status: 'assigned',
            assigned_to: 'Priya Sharma',
            photo_url: null
        },
        {
            id: '3',
            location: 'Mountain Community B',
            issue: 'No medical clinic - elderly need care',
            category: 'Healthcare',
            people_count: 75,
            urgency: 0.65,
            priority: 'Medium',
            status: 'pending',
            assigned_to: null,
            photo_url: null
        },
        {
            id: '4',
            location: 'Coastal Area C',
            issue: 'Homes destroyed by flood',
            category: 'Shelter',
            people_count: 300,
            urgency: 0.8,
            priority: 'High',
            status: 'pending',
            assigned_to: null,
            photo_url: null
        },
        {
            id: '5',
            location: 'Urban Slum D',
            issue: 'Children need school supplies',
            category: 'Education',
            people_count: 150,
            urgency: 0.4,
            priority: 'Medium',
            status: 'completed',
            assigned_to: 'Rajesh Kumar',
            photo_url: null
        }
    ];
    applyFilters();
}

/**
 * Apply filters to issues table
 */
function applyFilters() {
    const statusFilter = document.getElementById('filterStatus').value;
    const categoryFilter = document.getElementById('filterCategory').value;
    const priorityFilter = document.getElementById('filterPriority').value;

    let filtered = allIssues;

    if (statusFilter) {
        filtered = filtered.filter(i => i.status === statusFilter);
    }
    if (categoryFilter) {
        filtered = filtered.filter(i => i.category === categoryFilter);
    }
    if (priorityFilter) {
        filtered = filtered.filter(i => i.priority === priorityFilter);
    }

    renderIssues(filtered);
}

/**
 * Determine who can read an issue based on its status.
 */
function getReadAccess(status) {
    switch ((status || '').toLowerCase()) {
        case 'completed': return 'All';
        case 'assigned':  return 'Admin, NGO';
        case 'pending':   return 'Admin, NGO';
        default:          return 'Admin';
    }
}

/**
 * Render issues to table
 * @param {Array} issues - filtered list
 */
function renderIssues(issues) {
    const tbody = document.getElementById('issuesTableBody');
    const currentUser = window.RakshaAuth ? window.RakshaAuth.getUser() : null;
    const isVolunteer = currentUser && currentUser.role === 'volunteer';

    if (issues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center">No issues found</td></tr>';
        return;
    }

    tbody.innerHTML = issues.map((issue, index) => {
        // ── Photo cell (Change 2) ──────────────────────────────────────────
        const photoCell = issue.photo_url
            ? `<img
                    src="${escapeHtml(issue.photo_url)}"
                    alt="Photo — ${escapeHtml(issue.location)}"
                    class="issue-photo-thumb"
                    onerror="this.style.display='none';this.nextElementSibling.style.display='inline-flex';"
               ><span class="issue-photo-num" style="display:none;">#${index + 1}</span>`
            : `<span class="issue-photo-num">#${index + 1}</span>`;

        // ── Accessibility cell (Change 1) ─────────────────────────────────
        const readAccess  = getReadAccess(issue.status);
        const assignedTo  = escapeHtml(issue.assigned_to) || '—';
        const accessCell  = `
            <div class="access-read">
                <span class="access-label">Readers</span>
                <span class="badge badge-pending">${readAccess}</span>
            </div>
            <div class="access-divider"></div>
            <div class="access-assigned">
                <span class="access-label">Assigned</span>
                <span class="${issue.assigned_to ? 'badge badge-assigned' : 'text-muted'}">${assignedTo}</span>
            </div>`;

        // ── Actions cell (Change 3 — hide Match for volunteers) ───────────
        const viewBtn  = `<button class="btn btn-outline btn-sm" onclick="viewIssue('${issue.id}')">View</button>`;
        const matchBtn = !isVolunteer && issue.status === 'pending'
            ? `<button class="btn btn-primary btn-sm" onclick="matchVolunteer('${issue.id}')">Match</button>`
            : '';

        return `
            <tr>
                <td><strong>${escapeHtml(issue.location)}</strong></td>
                <td>${escapeHtml(issue.issue)}</td>
                <td><span class="badge badge-pending">${escapeHtml(issue.category)}</span></td>
                <td>${issue.people_count?.toLocaleString() || '—'}</td>
                <td>
                    <span class="badge ${API.getUrgencyBadgeClass(issue.urgency)}">
                        ${((issue.urgency > 1 ? issue.urgency : issue.urgency * 100)).toFixed(0)}%
                    </span>
                </td>
                <td>
                    <span class="badge ${API.getPriorityBadgeClass(issue.priority)}">
                        ${escapeHtml(issue.priority)}
                    </span>
                </td>
                <td>
                    <span class="badge ${API.getStatusBadgeClass(issue.status)}">
                        ${escapeHtml(issue.status)}
                    </span>
                </td>
                <td class="photo-cell">${photoCell}</td>
                <td class="access-cell">${accessCell}</td>
                <td>
                    <div style="display:flex;gap:0.4rem;flex-wrap:wrap;">
                        ${viewBtn}
                        ${matchBtn}
                    </div>
                </td>
            </tr>`;
    }).join('');
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

/**
 * View issue details
 */
async function viewIssue(issueId) {
    try {
        const response = await API.getIssue(issueId);
        if (response.success) {
            const issue = response.issue;
            alert(`Issue Details:\n\nLocation: ${issue.location}\nIssue: ${issue.issue}\nCategory: ${issue.category}\nPeople Affected: ${issue.people_count}\nUrgency: ${(issue.urgency * 100).toFixed(0)}%\nPriority: ${issue.priority}\nStatus: ${issue.status}`);
        }
    } catch (error) {
        alert('Error loading issue details');
    }
}

/**
 * Find volunteer match for an issue (NGO/Admin only — hidden from volunteers in UI)
 */
async function matchVolunteer(issueId) {
    try {
        const response = await API.getVolunteerMatch(issueId);

        if (response.success && response.best_match) {
            const match = response.best_match;
            const confirmAssign = confirm(
                `Best Match Found:\n\nVolunteer: ${match.volunteer_name}\nMatch Score: ${(match.match_score * 100).toFixed(0)}%\nDistance: ${match.distance_km} km\n\nAssign this volunteer?`
            );

            if (confirmAssign) {
                await API.assignTask(issueId, match.volunteer_id);
                alert('Task assigned successfully!');
                loadIssues();
            }
        } else {
            alert('No matching volunteers found for this issue.');
        }
    } catch (error) {
        alert('Error finding volunteer match: ' + error.message);
    }
}

// Initialization is handled by dashboard.html inline script (initAuthGuard → loadIssues)
