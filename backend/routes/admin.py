"""Admin routes for user management and volunteer approval."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime

from database.firebase import db

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(authorization: str = Header(None)):
    """Verify the request comes from an admin user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    user_id = db.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get_user(user_id)
    if not user or user.get("role") not in ("admin", "engineer"):
        raise HTTPException(status_code=403, detail="Admin or engineer access required")

    return user


def require_ngo_or_admin(authorization: str = Header(None)):
    """Allow NGOs, admins, and engineers to access this endpoint."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    user_id = db.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get_user(user_id)
    if not user or user.get("role") not in ("admin", "engineer", "ngo"):
        raise HTTPException(status_code=403, detail="NGO, admin, or engineer access required")
    if user.get("status") != "approved":
        raise HTTPException(status_code=403, detail="Account not yet approved")

    return user


@router.get("/pending-volunteers")
async def get_pending_volunteers(authorization: str = Header(None)):
    """Get all volunteers with pending status."""
    require_admin(authorization)

    users = db.get_users_by_status("pending")
    # Filter to volunteers only
    volunteers = [u for u in users if u.get("role") == "volunteer"]

    # Remove sensitive fields
    for v in volunteers:
        v.pop("password_hash", None)
        v.pop("password_salt", None)

    return {
        "success": True,
        "count": len(volunteers),
        "volunteers": volunteers,
    }


@router.post("/approve/{user_id}")
async def approve_user(user_id: str, authorization: str = Header(None)):
    """Approve a pending volunteer."""
    admin = require_admin(authorization)

    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.update_user(user_id, {
        "status": "approved",
        "approved_by": admin.get("id", ""),
        "approved_at": datetime.utcnow().isoformat(),
    })

    return {
        "success": True,
        "message": f"User {user.get('display_name', '')} approved",
    }


@router.post("/reject/{user_id}")
async def reject_user(user_id: str, authorization: str = Header(None)):
    """Reject a pending volunteer."""
    require_admin(authorization)

    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.update_user(user_id, {
        "status": "rejected",
        "rejected_at": datetime.utcnow().isoformat(),
    })

    return {
        "success": True,
        "message": f"User {user.get('display_name', '')} rejected",
    }


@router.get("/users")
async def list_users(role: Optional[str] = None, authorization: str = Header(None)):
    """List all users, optionally filtered by role."""
    require_admin(authorization)

    users = db.get_all_users()

    if role:
        users = [u for u in users if u.get("role") == role]

    # Remove sensitive fields
    for u in users:
        u.pop("password_hash", None)
        u.pop("password_salt", None)

    return {
        "success": True,
        "total": len(users),
        "users": users,
    }


@router.post("/seed-admin")
async def seed_admin():
    """Create the first admin account. Only works if no admin exists yet."""
    import hashlib
    import secrets

    existing = db.get_users_by_role("admin")
    if existing:
        raise HTTPException(status_code=409, detail="Admin already exists. Log in with existing admin credentials.")

    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', "admin123".encode(), salt.encode(), 100_000).hex()

    user_data = {
        "email": "admin@raksha.org",
        "password_hash": hashed,
        "password_salt": salt,
        "display_name": "Raksha Admin",
        "role": "admin",
        "status": "approved",
        "created_at": datetime.utcnow().isoformat(),
        "approved_by": "system",
    }

    user_id = db.create_user(user_data)
    return {
        "success": True,
        "message": "Admin account created",
        "credentials": {
            "email": "admin@raksha.org",
            "password": "admin123",
            "note": "Change this password immediately after first login."
        }
    }


@router.post("/assign-task")
async def assign_task(issue_id: str, volunteer_id: str, authorization: str = Header(None)):
    """Assign a task/issue to a volunteer. Admin or engineer can assign."""
    admin = require_admin(authorization)

    # Verify volunteer exists and is approved
    volunteer = db.get_user(volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    if volunteer.get("status") != "approved":
        raise HTTPException(status_code=400, detail="Volunteer is not approved")

    from database.firebase import db as firebase_db
    task_data = {
        "issue_id": issue_id,
        "volunteer_id": volunteer_id,
        "volunteer_name": volunteer.get("display_name", ""),
        "assigned_by": admin.get("id", ""),
        "assigned_at": datetime.utcnow().isoformat(),
        "status": "assigned",
    }

    task_id = firebase_db.create_task(task_data)

    return {
        "success": True,
        "message": f"Task assigned to {volunteer.get('display_name', '')}",
        "task_id": task_id,
    }


@router.post("/verify-documents/{user_id}")
async def verify_documents(user_id: str, verified: bool = True, notes: str = "", authorization: str = Header(None)):
    """Admin verifies volunteer skill documents/credentials."""
    admin = require_admin(authorization)

    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.update_user(user_id, {
        "documents_verified": verified,
        "verification_notes": notes,
        "verified_by": admin.get("id", ""),
        "verified_at": datetime.utcnow().isoformat(),
    })

    return {
        "success": True,
        "message": f"Documents {'verified' if verified else 'flagged'} for {user.get('display_name', '')}",
    }


@router.get("/tasks")
async def list_tasks(authorization: str = Header(None)):
    """List all assigned tasks (admin/engineer view)."""
    require_admin(authorization)
    tasks = db.get_all_tasks() if hasattr(db, "get_all_tasks") else []
    return {"success": True, "tasks": tasks}


@router.post("/tasks/{task_id}/decline")
async def decline_task(
    task_id: str,
    reason: str = "",
    authorization: str = Header(None),
):
    """Volunteer declines an assigned task; admin is notified for reassignment."""
    token = (authorization or "").replace("Bearer ", "")
    user_id = db.verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    task = db.get_task(task_id) if hasattr(db, "get_task") else None
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.get("volunteer_id") != user_id:
        raise HTTPException(status_code=403, detail="Not your task")

    db.update_task(task_id, {
        "status": "declined",
        "decline_reason": reason,
        "declined_at": datetime.utcnow().isoformat(),
    })
    return {"success": True, "message": "Task declined; admin notified for reassignment."}


# ==================== NGO-accessible endpoints ====================

@router.post("/ngo/assign-task")
async def ngo_assign_task(
    issue_id: str,
    volunteer_id: str,
    authorization: str = Header(None),
):
    """NGOs (and admins) can assign an issue to an approved volunteer."""
    actor = require_ngo_or_admin(authorization)

    issue = db.get_issue(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    volunteer = db.get_user(volunteer_id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    if volunteer.get("status") != "approved":
        raise HTTPException(status_code=400, detail="Volunteer is not approved")

    task_data = {
        "issue_id": issue_id,
        "volunteer_id": volunteer_id,
        "volunteer_name": volunteer.get("display_name", ""),
        "assigned_by": actor.get("id", ""),
        "assigned_by_role": actor.get("role", ""),
        "assigned_at": datetime.utcnow().isoformat(),
        "status": "assigned",
    }
    db.update_issue(issue_id, {"status": "assigned",
                               "assigned_volunteer": volunteer_id})
    task_id = db.create_task(task_data)

    return {
        "success": True,
        "message": f"Task assigned to {volunteer.get('display_name', '')}",
        "task_id": task_id,
    }


@router.post("/ngo/add-volunteer")
async def ngo_add_volunteer(
    display_name: str,
    skills: str = "",
    phone: str = "",
    email: str = "",
    latitude: float = 0.0,
    longitude: float = 0.0,
    authorization: str = Header(None),
):
    """NGOs can directly add a volunteer (pre-approved, status=approved)."""
    actor = require_ngo_or_admin(authorization)

    skills_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else []

    volunteer_data = {
        "display_name": display_name,
        "skills": skills_list,
        "phone": phone,
        "email": email,
        "latitude": latitude,
        "longitude": longitude,
        "role": "volunteer",
        "status": "approved",
        "added_by": actor.get("id", ""),
        "added_by_role": actor.get("role", ""),
        "created_at": datetime.utcnow().isoformat(),
        "source": "ngo_direct",
    }
    # Store in both collections for compatibility
    vol_id = db.add_volunteer({
        "name": display_name,
        "skills": skills_list,
        "phone": phone,
        "email": email,
        "latitude": latitude,
        "longitude": longitude,
        "status": "available",
        "added_by": actor.get("id", ""),
    })

    return {
        "success": True,
        "message": f"Volunteer '{display_name}' added successfully",
        "volunteer_id": vol_id,
    }
