"""Routes for AI classification and processing."""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from pydantic import BaseModel

from database.firebase import db
from services.ai_service import process_issue, classify_issue, calculate_urgency
from models.schema import ClassificationResult

router = APIRouter(prefix="/ai", tags=["AI Processing"])


class ClassifyRequest(BaseModel):
    """Request model for issue classification."""
    text: str
    people_count: int = 100


@router.post("/classify", response_model=ClassificationResult)
async def classify_issue_endpoint(req: ClassifyRequest = Body(...)):
    """
    Classify an issue text and return category, urgency, and priority.

    Example:
    - Input: "No clean water for 100 people"
    - Output: {"category": "Water", "urgency": 0.75, "priority": "High"}
    """
    try:
        result = process_issue(req.text, req.people_count)
        return ClassificationResult(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classify/batch")
async def batch_classify_pending_issues():
    """
    Classify all pending issues that haven't been processed yet.

    Useful for re-processing or initial batch classification.
    """
    try:
        issues = db.get_all_issues()
        updated = []

        for issue in issues:
            # Re-classify based on issue text
            issue_text = issue.get("issue", "")
            people_count = issue.get("people_count", 100)

            classification = process_issue(issue_text, people_count)

            # Update in database
            db.update_issue(issue["id"], classification)

            updated.append({
                "issue_id": issue["id"],
                "location": issue.get("location", ""),
                "classification": classification
            })

        return {
            "success": True,
            "message": f"Classified {len(updated)} issues",
            "results": updated
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_ai_stats():
    """
    Get statistics about classified issues.

    Returns category distribution and urgency breakdown.
    """
    try:
        issues = db.get_all_issues()

        # Category counts
        category_counts = {}
        priority_counts = {}
        urgency_levels = {"high": 0, "medium": 0, "low": 0}

        for issue in issues:
            category = issue.get("category", "Unknown")
            priority = issue.get("priority", "Unknown")
            urgency = issue.get("urgency", 0)

            category_counts[category] = category_counts.get(category, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

            if urgency >= 0.7:
                urgency_levels["high"] += 1
            elif urgency >= 0.4:
                urgency_levels["medium"] += 1
            else:
                urgency_levels["low"] += 1

        return {
            "total_issues": len(issues),
            "by_category": category_counts,
            "by_priority": priority_counts,
            "urgency_distribution": urgency_levels
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
