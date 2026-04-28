"""Routes for NGO data upload (form and CSV)."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import csv
import io

from database.firebase import db
from services.ai_service import process_issue
from models.schema import NGOData

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/form")
async def upload_form(
    location: str = Form(...),
    issue: str = Form(...),
    people_count: int = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    contact_info: Optional[str] = Form(None)
):
    """
    Upload a single NGO issue via form.

    Automatically classifies the issue and calculates urgency.
    """
    try:
        # Process issue through AI service
        classification = process_issue(issue, people_count)

        # Create issue data
        issue_data = {
            "location": location,
            "issue": issue,
            "people_count": people_count,
            "latitude": latitude,
            "longitude": longitude,
            "contact_info": contact_info,
            "category": classification["category"],
            "urgency": classification["urgency"],
            "priority": classification["priority"],
            "status": "pending"
        }

        # Store in Firestore
        issue_id = db.add_issue(issue_data)

        return {
            "success": True,
            "message": "Issue uploaded successfully",
            "issue_id": issue_id,
            "classification": classification
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload multiple NGO issues via CSV file.

    CSV should have columns: location, issue, people_count, latitude, longitude, contact_info
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        contents = await file.read()
        csv_content = contents.decode('utf-8')

        reader = csv.DictReader(io.StringIO(csv_content))
        issues = []
        results = []

        for row in reader:
            try:
                # Parse row data
                location = row.get('location', '')
                issue = row.get('issue', '')
                people_count = int(row.get('people_count', 0))
                latitude = float(row.get('latitude', 0))
                longitude = float(row.get('longitude', 0))
                contact_info = row.get('contact_info', None)

                # Validate required fields
                if not location or not issue or people_count <= 0:
                    results.append({
                        "row": row,
                        "status": "skipped",
                        "reason": "Missing required fields"
                    })
                    continue

                # Process through AI service
                classification = process_issue(issue, people_count)

                issue_data = {
                    "location": location,
                    "issue": issue,
                    "people_count": people_count,
                    "latitude": latitude,
                    "longitude": longitude,
                    "contact_info": contact_info,
                    "category": classification["category"],
                    "urgency": classification["urgency"],
                    "priority": classification["priority"],
                    "status": "pending"
                }

                issues.append(issue_data)
                results.append({
                    "location": location,
                    "status": "processed",
                    "classification": classification
                })

            except Exception as e:
                results.append({
                    "row": row,
                    "status": "error",
                    "reason": str(e)
                })

        # Batch add to Firestore
        if issues:
            issue_ids = db.batch_add_issues(issues)
            return {
                "success": True,
                "message": f"Processed {len(results)} rows, added {len(issues)} issues",
                "results": results,
                "issue_ids": issue_ids
            }

        return {
            "success": False,
            "message": "No valid issues found in CSV",
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
