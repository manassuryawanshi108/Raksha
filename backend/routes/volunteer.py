"""Routes for volunteer registration, matching, and task assignment."""

from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Dict, Any, Optional

from database.firebase import db
from services.matching import match_volunteers_to_issue, get_best_match
from models.schema import Volunteer, TaskAssignment, MatchResult

router = APIRouter(prefix="/volunteer", tags=["Volunteers"])


@router.post("/register")
async def register_volunteer(
    name: str = Body(None),
    skills: List[str] = Body(None),
    latitude: float = Body(None),
    longitude: float = Body(None),
    phone: Optional[str] = Body(None),
    email: Optional[str] = Body(None),
    # Fallback to query params for backwards compatibility
    name_q: Optional[str] = Query(None, alias="name"),
    skills_q: Optional[str] = Query(None, alias="skills"),
    latitude_q: Optional[float] = Query(None, alias="latitude"),
    longitude_q: Optional[float] = Query(None, alias="longitude"),
    phone_q: Optional[str] = Query(None, alias="phone"),
    email_q: Optional[str] = Query(None, alias="email")
):
    """Register a new volunteer."""
    # Use body params if provided, otherwise fall back to query params
    if name is None and name_q is not None:
        name = name_q
    if skills is None and skills_q is not None:
        import json
        skills = json.loads(skills_q)
    if latitude is None and latitude_q is not None:
        latitude = latitude_q
    if longitude is None and longitude_q is not None:
        longitude = longitude_q
    if phone is None and phone_q is not None:
        phone = phone_q
    if email is None and email_q is not None:
        email = email_q

    try:
        volunteer_data = {
            "name": name,
            "skills": skills,
            "latitude": latitude,
            "longitude": longitude,
            "phone": phone,
            "email": email,
            "status": "available"
        }

        volunteer_id = db.add_volunteer(volunteer_data)

        return {
            "success": True,
            "message": "Volunteer registered successfully",
            "volunteer_id": volunteer_id,
            "data": volunteer_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_volunteers():
    """Get all registered volunteers."""
    try:
        volunteers = db.get_all_volunteers()
        return {
            "success": True,
            "count": len(volunteers),
            "volunteers": volunteers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
async def list_available_volunteers():
    """Get volunteers who are available for assignment."""
    try:
        volunteers = db.get_available_volunteers()
        return {
            "success": True,
            "count": len(volunteers),
            "volunteers": volunteers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match/{issue_id}")
async def match_volunteer(issue_id: str):
    """
    Find the best matching volunteer for a specific issue.

    Returns match score, distance, and volunteer details.
    """
    try:
        # Get the issue
        issue = db.get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")

        # Get available volunteers
        volunteers = db.get_available_volunteers()
        if not volunteers:
            return {
                "success": False,
                "message": "No available volunteers",
                "matches": []
            }

        # Find best match
        best_match = get_best_match(issue, volunteers)

        return {
            "success": True,
            "issue_id": issue_id,
            "best_match": best_match
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match-all")
async def match_all_pending_issues():
    """
    Get match recommendations for all pending issues.

    Returns top 3 matches for each issue.
    """
    try:
        # Get pending issues
        issues = db.get_pending_issues()

        # Get available volunteers
        volunteers = db.get_available_volunteers()

        if not volunteers:
            return {
                "success": False,
                "message": "No available volunteers",
                "matches": []
            }

        all_matches = []
        for issue in issues:
            matches = match_volunteers_to_issue(issue, volunteers)[:3]  # Top 3
            all_matches.append({
                "issue_id": issue["id"],
                "location": issue.get("location", ""),
                "category": issue.get("category", ""),
                "matches": matches
            })

        return {
            "success": True,
            "total_issues": len(issues),
            "matches": all_matches
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign")
async def assign_task(
    issue_id: str,
    volunteer_id: str
):
    """
    Assign a task (issue) to a volunteer.

    Updates both the issue status and creates a task record.
    """
    try:
        # Verify issue exists
        issue = db.get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")

        # Verify volunteer exists
        volunteer = db.get_volunteer(volunteer_id)
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")

        # Update issue status
        db.update_issue(issue_id, {
            "status": "assigned",
            "assigned_volunteer": volunteer_id,
            "assigned_volunteer_name": volunteer.get("name", "")
        })

        # Update volunteer status
        db.update_volunteer(volunteer_id, {"status": "assigned"})

        # Create task record
        task_data = {
            "issue_id": issue_id,
            "volunteer_id": volunteer_id,
            "issue_location": issue.get("location", ""),
            "issue_category": issue.get("category", ""),
            "status": "assigned",
            "assigned_at": "now"  # Could use datetime
        }
        task_id = db.create_task(task_data)

        return {
            "success": True,
            "message": f"Task assigned to {volunteer.get('name', '')}",
            "task_id": task_id,
            "issue_id": issue_id,
            "volunteer_id": volunteer_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/all")
async def get_all_tasks():
    """Get ALL tasks — for NGO/admin task roster view (no auth restriction)."""
    try:
        tasks = db.get_all_tasks()
        return {
            "success": True,
            "count": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{volunteer_id}")
async def get_volunteer_tasks(volunteer_id: str):
    """Get all tasks assigned to a specific volunteer."""
    try:
        tasks = db.get_tasks_by_volunteer(volunteer_id)
        return {
            "success": True,
            "volunteer_id": volunteer_id,
            "count": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/task/{task_id}/complete")
async def complete_task(task_id: str):
    """Mark a task as completed."""
    try:
        task = db.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        db.update_task(task_id, {"status": "completed"})

        # Also mark the issue as completed if we can find it
        issue_id = task.get("issue_id")
        if issue_id:
            db.update_issue(issue_id, {"status": "completed"})

        return {
            "success": True,
            "message": "Task marked as completed",
            "task_id": task_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
