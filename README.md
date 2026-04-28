# Raksha

AI-powered humanitarian resource platform — connecting NGOs with skilled volunteers.

## Features

- 📊 **Dashboard** — Real-time overview of all issues with urgency levels
- 📍 **Interactive Map** — Visualize issues on Google Maps with color-coded markers
- 📤 **Data Upload** — Single form or bulk CSV upload with AI classification
- 🤖 **AI Processing** — Automatic issue categorization and urgency scoring
- 👥 **Volunteer Matching** — Smart matching based on skills and distance
- 🔐 **Authentication** — Role-based login for NGOs, Volunteers, and Admins
- 🛡️ **Access Control** — NGOs submit issues, volunteers request to help, admin approves

## User Roles

| Role | Can Do |
|------|--------|
| **NGO** | Submit problems/issues, upload CSV, view dashboard & map |
| **Volunteer** | Request to help on issues (after admin approval) |
| **Admin** | Approve/reject volunteers, manage users, full access |

## Quick Start

### Prerequisites

- Python 3.8+
- Firebase account (Firestore)
- Google Maps API key (for map feature)

### 1. Clone & Setup

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Firebase

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Firestore Database
3. Generate a service account key (JSON)
4. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/serviceAccountKey.json"
   ```

### 3. Run Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access API docs at: http://localhost:8000/docs

### 4. Run Frontend

```bash
cd frontend
python -m http.server 8080
```

Open http://localhost:8080 in your browser.

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   ├── routes/
│   │   ├── auth.py          # Register / Login
│   │   ├── admin.py         # User management & approvals
│   │   ├── issues.py        # Issue CRUD
│   │   ├── upload.py        # Form & CSV upload
│   │   ├── ai.py            # AI classification
│   │   └── volunteer.py     # Volunteer management
│   ├── database/firebase.py # Firestore operations
│   ├── models/schema.py     # Pydantic schemas
│   └── requirements.txt
└── frontend/
    ├── index.html           # Landing page
    ├── login.html           # Auth (login/register)
    ├── admin.html           # Admin panel
    ├── pending.html         # Volunteer pending page
    ├── dashboard.html       # Issues dashboard
    ├── upload.html          # Data upload
    ├── map.html             # Google Maps
    ├── volunteer.html       # Volunteer management
    ├── assets/logo.png      # Raksha logo
    ├── js/                  # JavaScript modules
    └── css/styles.css       # Design system
```

## Access Control Flow

1. **NGO registers** → auto-approved → can submit issues immediately
2. **Volunteer registers** → status = `pending` → must wait for admin approval
3. **Admin approves volunteer** → status = `approved` → volunteer can request to help
4. **Admin rejects volunteer** → status = `rejected` → access denied

## License

MIT License
