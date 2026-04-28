"""Routes for retrieving and managing issues."""

from fastapi import APIRouter, HTTPException
from typing import List, Optional

from database.firebase import db

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.get("/list")
async def get_all_issues(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None
):
    """
    Get all issues with optional filters.

    Filters:
    - status: pending, assigned, completed
    - category: Water, Food, Healthcare, Shelter, Education
    - priority: High, Medium, Low
    """
    try:
        issues = db.get_all_issues()

        # Apply filters
        if status:
            issues = [i for i in issues if i.get("status") == status]
        if category:
            issues = [i for i in issues if i.get("category") == category]
        if priority:
            issues = [i for i in issues if i.get("priority") == priority]

        # Sort by urgency (highest first)
        issues.sort(key=lambda x: x.get("urgency", 0), reverse=True)

        return {
            "success": True,
            "count": len(issues),
            "issues": issues
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{issue_id}")
async def get_issue(issue_id: str):
    """Get a specific issue by ID."""
    try:
        issue = db.get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")

        return {
            "success": True,
            "issue": issue
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/map/markers")
async def get_map_markers():
    """
    Get all issues formatted for Google Maps markers.

    Returns location, coordinates, urgency, and category for each issue.
    """
    try:
        issues = db.get_all_issues()

        markers = []
        for issue in issues:
            markers.append({
                "id": issue["id"],
                "location": issue.get("location", ""),
                "lat": issue.get("latitude", 0),
                "lng": issue.get("longitude", 0),
                "urgency": issue.get("urgency", 0),
                "category": issue.get("category", ""),
                "priority": issue.get("priority", ""),
                "status": issue.get("status", "pending")
            })

        return {
            "success": True,
            "count": len(markers),
            "markers": markers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{issue_id}")
async def delete_issue(issue_id: str):
    """Delete an issue."""
    try:
        db.delete_issue(issue_id)
        return {
            "success": True,
            "message": "Issue deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_issues_summary():
    """Get summary statistics for dashboard."""
    try:
        issues = db.get_all_issues()

        total = len(issues)
        pending = sum(1 for i in issues if i.get("status") == "pending")
        assigned = sum(1 for i in issues if i.get("status") == "assigned")
        high_priority = sum(1 for i in issues if i.get("priority") == "High")

        # Total people affected
        total_people = sum(i.get("people_count", 0) for i in issues)

        return {
            "success": True,
            "summary": {
                "total_issues": total,
                "pending_issues": pending,
                "assigned_issues": assigned,
                "high_priority_issues": high_priority,
                "total_people_affected": total_people
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
