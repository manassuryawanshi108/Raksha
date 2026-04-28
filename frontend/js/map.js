/**
 * Map JavaScript - Google Maps integration with issue markers
 */

let map;
let markers = [];
let allMarkersData = [];

/**
 * Mobile menu toggle
 */
function toggleMenu() {
    document.getElementById('navbarNav').classList.toggle('active');
}

/**
 * Initialize Google Maps
 */
function initMap() {
    // Default center (India - can be changed based on your region)
    const defaultCenter = { lat: 20.5937, lng: 78.9629 };

    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 5,
        center: defaultCenter,
        styles: [
            {
                featureType: 'poi',
                elementType: 'labels',
                stylers: [{ visibility: 'off' }]
            }
        ]
    });

    // Load markers after map initializes
    loadMapMarkers();
}

/**
 * Load markers from API
 */
async function loadMapMarkers() {
    try {
        const response = await API.getMapMarkers();

        if (response.success) {
            allMarkersData = response.markers;
            clearMarkers();
            createMarkers(allMarkersData);
        } else {
            console.error('Failed to load markers');
        }
    } catch (error) {
        console.error('Error loading markers:', error);
        // Load demo data for demonstration
        loadDemoMarkers();
    }
}

/**
 * Load demo markers when backend is unavailable
 */
function loadDemoMarkers() {
    allMarkersData = [
        {
            id: '1',
            location: 'Village A, Rural District',
            lat: 28.6139,
            lng: 77.2090,
            urgency: 0.75,
            category: 'Water',
            priority: 'High',
            status: 'pending'
        },
        {
            id: '2',
            location: 'Refugee Camp Sector 3',
            lat: 28.5355,
            lng: 77.3910,
            urgency: 0.9,
            category: 'Food',
            priority: 'High',
            status: 'assigned'
        },
        {
            id: '3',
            location: 'Mountain Community B',
            lat: 30.0668,
            lng: 79.0193,
            urgency: 0.65,
            category: 'Healthcare',
            priority: 'Medium',
            status: 'pending'
        },
        {
            id: '4',
            location: 'Coastal Area C',
            lat: 19.0760,
            lng: 72.8777,
            urgency: 0.8,
            category: 'Shelter',
            priority: 'High',
            status: 'pending'
        },
        {
            id: '5',
            location: 'Urban Slum D',
            lat: 18.9388,
            lng: 72.8354,
            urgency: 0.4,
            category: 'Education',
            priority: 'Medium',
            status: 'completed'
        },
        {
            id: '6',
            location: 'Desert Region E',
            lat: 26.9124,
            lng: 75.7873,
            urgency: 0.85,
            category: 'Water',
            priority: 'High',
            status: 'pending'
        }
    ];
    clearMarkers();
    createMarkers(allMarkersData);
}

/**
 * Clear all markers from map
 */
function clearMarkers() {
    markers.forEach(marker => marker.setMap(null));
    markers = [];
}

/**
 * Create markers on the map
 */
function createMarkers(markersData) {
    markersData.forEach(data => {
        const markerColor = API.getMarkerColor(data.urgency);

        const marker = new google.maps.Marker({
            position: { lat: data.lat, lng: data.lng },
            map: map,
            title: data.location,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                scale: 10,
                fillColor: markerColor,
                fillOpacity: 1,
                strokeWeight: 2,
                strokeColor: '#ffffff'
            }
        });

        // Create info window content — Change 5b: full field set + optional photo
        const photoHtml = data.photo_url
            ? `<img src="${escapeHtml(data.photo_url)}"
                    alt="Photo — ${escapeHtml(data.location)}"
                    style="max-width:120px;max-height:80px;object-fit:cover;display:block;margin:6px 0;"
                    onerror="this.style.display='none';">`
            : '';

        const infoContent = `
            <div style="padding: 10px; max-width: 260px; font-family: sans-serif;">
                <h3 style="margin: 0 0 6px 0; font-size: 15px;">${escapeHtml(data.location)}</h3>
                ${photoHtml}
                <p style="margin: 4px 0; font-size: 13px;"><strong>Issue:</strong> ${escapeHtml(data.issue || data.description || '—')}</p>
                <p style="margin: 4px 0; font-size: 13px;"><strong>Category:</strong> ${escapeHtml(data.category)}</p>
                <p style="margin: 4px 0; font-size: 13px;"><strong>Urgency:</strong> ${(data.urgency * 100).toFixed(0)}%</p>
                <p style="margin: 4px 0; font-size: 13px;"><strong>Priority:</strong> ${escapeHtml(data.priority)}</p>
                <p style="margin: 4px 0; font-size: 13px;"><strong>Status:</strong> ${escapeHtml(data.status)}</p>
            </div>
        `;

        const infoWindow = new google.maps.InfoWindow({
            content: infoContent
        });

        marker.addListener('click', () => {
            // Close all other info windows
            markers.forEach(m => {
                if (m.infoWindow) m.infoWindow.close();
            });
            infoWindow.open(map, marker);
        });

        // Store reference to info window
        marker.infoWindow = infoWindow;
        markers.push(marker);
    });

    // Fit map to show all markers
    if (markers.length > 0) {
        const bounds = new google.maps.LatLngBounds();
        markers.forEach(marker => bounds.extend(marker.getPosition()));
        map.fitBounds(bounds);
    }
}

/**
 * Filter markers based on selections
 */
function filterMarkers() {
    const categoryFilter = document.getElementById('filterCategory').value;
    const priorityFilter = document.getElementById('filterPriority').value;
    const statusFilter = document.getElementById('filterStatus').value;

    let filtered = allMarkersData;

    if (categoryFilter) {
        filtered = filtered.filter(m => m.category === categoryFilter);
    }
    if (priorityFilter) {
        filtered = filtered.filter(m => m.priority === priorityFilter);
    }
    if (statusFilter) {
        filtered = filtered.filter(m => m.status === statusFilter);
    }

    clearMarkers();
    createMarkers(filtered);
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

// Handle case when Google Maps API fails to load
window.gm_authFailure = function() {
    document.getElementById('apiKeyWarning').classList.remove('hidden');
    document.getElementById('map').innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f3f4f6;">
            <div style="text-align: center; padding: 2rem;">
                <h3 style="color: #666;">Map Not Available</h3>
                <p style="color: #999;">Please add a valid Google Maps API key</p>
            </div>
        </div>
    `;
};

// Initialize map when page loads (if API is available)
if (typeof google === 'undefined') {
    // API not loaded yet, show warning
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (typeof google === 'undefined') {
                document.getElementById('apiKeyWarning').classList.remove('hidden');
            }
        }, 3000);
    });
}
