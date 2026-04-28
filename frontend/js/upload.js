/**
 * Upload Page JavaScript - Form and CSV upload handling
 */

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
    container.innerHTML = `
        <div class="alert alert-${type}">
            ${escapeHtml(message)}
        </div>
    `;
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

/**
 * Handle form submission
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    const formData = {
        location: document.getElementById('location').value,
        issue: document.getElementById('issue').value,
        people_count: parseInt(document.getElementById('peopleCount').value),
        latitude: parseFloat(document.getElementById('latitude').value),
        longitude: parseFloat(document.getElementById('longitude').value),
        contact_info: document.getElementById('contactInfo').value || null
    };

    try {
        const response = await API.uploadIssue(formData);

        if (response.success) {
            showAlert(`Issue uploaded successfully! ID: ${response.issue_id}. Category: ${response.classification.category}, Urgency: ${(response.classification.urgency * 100).toFixed(0)}%`);
            document.getElementById('uploadForm').reset();
        }
    } catch (error) {
        showAlert('Error uploading issue: ' + error.message, 'error');
    }
}

/**
 * Handle CSV file preview
 */
document.getElementById('csvFile')?.addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        const lines = content.split('\n').slice(0, 6);

        const preview = document.getElementById('csvPreview');
        preview.innerHTML = '<pre style="margin: 0; font-family: monospace;">' +
            lines.map(line => escapeHtml(line)).join('\n') +
            (content.split('\n').length > 5 ? '\n...' : '') +
            '</pre>';
    };
    reader.readAsText(file);
});

/**
 * Handle CSV upload
 */
async function handleCSVUpload() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];

    if (!file) {
        showAlert('Please select a CSV file', 'error');
        return;
    }

    try {
        showAlert('Uploading CSV...', 'success');
        const response = await API.uploadCSV(file);

        if (response.success) {
            showAlert(`CSV processed! Added ${response.issue_ids?.length || 0} issues. ${response.results?.filter(r => r.status === 'skipped').length || 0} rows skipped.`);
            fileInput.value = '';
            document.getElementById('csvPreview').innerHTML = '<em class="text-muted">Select a file to preview</em>';
        } else {
            showAlert('CSV upload failed: ' + response.message, 'error');
        }
    } catch (error) {
        showAlert('Error uploading CSV: ' + error.message, 'error');
    }
}

/**
 * Download sample CSV template
 */
function downloadSampleCSV() {
    const sampleCSV = `location,issue,people_count,latitude,longitude,contact_info
"Village A, Rural District","No clean water for 100 people. The well is contaminated.",100,28.6139,77.2090,"village.a@ngo.org"
"Refugee Camp Sector 3","Food shortage critical. 500 families need rations.",2500,28.5355,77.3910,"sector3@refugeecamp.org"
"Mountain Community B","No doctor or medical clinic. Elderly need care.",75,30.0668,79.0193,"community.b@mountain.org"
"Coastal Area C","Homes destroyed by flood. Need emergency shelter.",300,19.0760,72.8777,"area.c@coastal.org"
"Urban Slum D","Children have no access to school. Need books.",150,18.9388,72.8354,"slum.d@urban.org"`;

    const blob = new Blob([sampleCSV], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_ngo_data.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Test AI classification
 */
async function testClassification() {
    const text = document.getElementById('testText').value;
    const peopleCount = parseInt(document.getElementById('testPeople').value) || 100;

    if (!text.trim()) {
        document.getElementById('classificationResult').innerHTML =
            '<em class="text-muted">Please enter some text</em>';
        return;
    }

    try {
        const result = await API.classifyIssue(text, peopleCount);

        document.getElementById('classificationResult').innerHTML = `
            <h4 style="margin-bottom: 0.5rem;">Classification Result</h4>
            <p><strong>Category:</strong> <span class="badge badge-pending">${result.category}</span></p>
            <p><strong>Urgency:</strong> <span class="badge ${API.getUrgencyBadgeClass(result.urgency)}">${(result.urgency * 100).toFixed(0)}%</span></p>
            <p><strong>Priority:</strong> <span class="badge ${API.getPriorityBadgeClass(result.priority)}">${result.priority}</span></p>
        `;
    } catch (error) {
        document.getElementById('classificationResult').innerHTML =
            `<p class="text-danger">Error: ${error.message}</p>`;
    }
}
