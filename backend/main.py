"""FastAPI backend for Raksha — AI-powered humanitarian resource platform."""

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

# Import routes
from routes import upload, ai, volunteer, issues, auth, admin


def _seed_admin() -> None:
    """Create a default admin account if none exists yet."""
    from database.firebase import db
    from routes.auth import hash_password, generate_token
    from datetime import datetime

    ADMIN_EMAIL = "admin@raksha.dev"
    ADMIN_PASS  = "Admin@1234"

    if db.get_user_by_email(ADMIN_EMAIL):
        print("[STARTUP] Admin account already exists — skipping seed.")
        return

    hashed, salt = hash_password(ADMIN_PASS)
    user_data = {
        "email": ADMIN_EMAIL,
        "password_hash": hashed,
        "password_salt": salt,
        "display_name": "Super Admin",
        "role": "admin",
        "status": "approved",
        "created_at": datetime.utcnow().isoformat(),
        "approved_by": "system",
    }
    user_id = db.create_user(user_data)
    print(f"[STARTUP] ✅ Admin account created — email: {ADMIN_EMAIL}  password: {ADMIN_PASS}  (id: {user_id})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_admin()
    yield


# Initialize FastAPI app
app = FastAPI(
    title="Raksha",
    description="AI-powered platform for matching humanitarian needs with volunteers and resources",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS — default covers all common local dev setups
_default_origins = ",".join([
    "http://localhost:8080", "http://127.0.0.1:8080",
    "http://localhost:5500", "http://127.0.0.1:5500",
    "http://localhost:5501", "http://127.0.0.1:5501",
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:8000", "http://127.0.0.1:8000",
    "null",  # file:// origin
])
allowed_origins = os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(upload.router)
app.include_router(ai.router)
app.include_router(volunteer.router)
app.include_router(issues.router)


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "Raksha API — Humanitarian Resource Platform",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Seed data endpoint (for development - admin only)
@app.post("/seed")
async def seed_data(authorization: str = Header(None)):
    """Seed database with sample data for testing - requires admin token."""
    from database.firebase import db
    from utils.datasets import seed_database

    # Verify authorization
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    # Verify token and check if admin
    user_id = db.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get_user(user_id)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        result = seed_database(db)
        return {
            "success": True,
            "message": "Database seeded successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
