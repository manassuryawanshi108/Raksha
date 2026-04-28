"""Routes for user authentication — register, login, and profile."""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import hashlib
import secrets

from database.firebase import db

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    """Registration payload."""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    display_name: str = Field(..., description="Display name")
    role: str = Field(..., description="Role: 'ngo' or 'volunteer'")
    # NGO-specific
    organization_name: Optional[str] = None
    registration_number: Optional[str] = None
    # Volunteer-specific
    skills: Optional[List[str]] = None
    experience_level: Optional[str] = None


class LoginRequest(BaseModel):
    """Login payload."""
    email: str
    password: str


def hash_password(password: str, salt: str = None) -> tuple:
    """Hash a password with a salt. Returns (hashed, salt)."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100_000).hex()
    return hashed, salt


def generate_token(user_id: str) -> str:
    """Generate a simple session token."""
    return f"{user_id}:{secrets.token_hex(32)}"


@router.post("/register")
async def register(req: RegisterRequest):
    """Register a new user (NGO or Volunteer)."""
    # Validate role
    if req.role not in ("ngo", "volunteer"):
        raise HTTPException(status_code=400, detail="Role must be 'ngo' or 'volunteer'")

    # Check for duplicate email
    existing = db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Hash password
    hashed, salt = hash_password(req.password)

    # Determine initial status
    # NGOs are approved immediately; volunteers start as pending
    status = "approved" if req.role == "ngo" else "pending"

    user_data = {
        "email": req.email,
        "password_hash": hashed,
        "password_salt": salt,
        "display_name": req.display_name,
        "role": req.role,
        "status": status,
        "created_at": datetime.utcnow().isoformat(),
        "approved_by": None,
    }

    # Role-specific fields
    if req.role == "ngo":
        user_data["organization_name"] = req.organization_name or ""
        user_data["registration_number"] = req.registration_number or ""
    else:
        user_data["skills"] = req.skills or []
        user_data["experience_level"] = req.experience_level or "beginner"

    user_id = db.create_user(user_data)
    token = generate_token(user_id)

    # Store token
    db.store_token(token, user_id)

    # Return user (exclude password fields)
    safe_user = {k: v for k, v in user_data.items() if k not in ("password_hash", "password_salt")}
    safe_user["id"] = user_id

    return {
        "success": True,
        "message": f"Account created as {req.role}. {'Awaiting admin approval.' if status == 'pending' else 'You can now access the platform.'}",
        "user": safe_user,
        "token": token,
    }


@router.post("/login")
async def login(req: LoginRequest):
    """Log in with email and password."""
    user = db.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password
    hashed, _ = hash_password(req.password, user.get("password_salt", ""))
    if hashed != user.get("password_hash", ""):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = generate_token(user["id"])
    db.store_token(token, user["id"])

    safe_user = {k: v for k, v in user.items() if k not in ("password_hash", "password_salt")}

    return {
        "success": True,
        "user": safe_user,
        "token": token,
    }


@router.get("/me")
async def get_current_user(authorization: str = Header(None)):
    """Get current user from Authorization header (Bearer token)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header provided")

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    user_id = db.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    safe_user = {k: v for k, v in user.items() if k not in ("password_hash", "password_salt")}
    return {"success": True, "user": safe_user}
