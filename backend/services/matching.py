"""Volunteer matching service based on skills and distance."""

from typing import List, Dict, Any, Tuple
from math import radians, sin, cos, sqrt, atan2


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points using Haversine formula.

    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def calculate_skill_match(volunteer_skills: List[str], issue_category: str) -> float:
    """
    Calculate skill match score between volunteer and issue.

    Args:
        volunteer_skills: List of volunteer's skills
        issue_category: Category of the issue

    Returns:
        Skill match score between 0 and 1
    """
    # Map categories to relevant skills
    category_skills = {
        "Water": ["plumbing", "engineering", "water treatment", "construction"],
        "Food": ["cooking", "agriculture", "nutrition", "logistics", "distribution"],
        "Healthcare": ["medical", "nursing", "doctor", "first aid", "pharmacy"],
        "Shelter": ["construction", "carpentry", "engineering", "architecture"],
        "Education": ["teaching", "tutoring", "education", "training"]
    }

    relevant_skills = category_skills.get(issue_category, [])

    if not relevant_skills:
        return 0.5  # Default score if no category match

    volunteer_skills_lower = [s.lower() for s in volunteer_skills]
    relevant_skills_lower = [s.lower() for s in relevant_skills]

    matches = sum(1 for skill in volunteer_skills_lower
                  if any(rel_skill in skill or skill in rel_skill
                         for rel_skill in relevant_skills_lower))

    return min(1.0, matches / max(1, len(relevant_skills)))


def calculate_distance_score(distance_km: float) -> float:
    """
    Convert distance to a score (closer = higher score).

    Args:
        distance_km: Distance in kilometers

    Returns:
        Distance score between 0 and 1
    """
    # Score decreases with distance
    # 0km = 1.0, 50km = 0.5, 100km+ = 0.1
    if distance_km <= 0:
        return 1.0
    elif distance_km >= 100:
        return 0.1
    else:
        return 1.0 - (distance_km / 100) * 0.9


def match_volunteers_to_issue(
    issue: Dict[str, Any],
    volunteers: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Match volunteers to an issue based on skills and distance.

    Args:
        issue: Issue data with category, lat, lng
        volunteers: List of volunteer data

    Returns:
        Sorted list of matches with scores
    """
    matches = []

    issue_lat = issue.get("latitude", 0)
    issue_lng = issue.get("longitude", 0)
    issue_category = issue.get("category", "Other")

    for volunteer in volunteers:
        vol_lat = volunteer.get("latitude", 0)
        vol_lng = volunteer.get("longitude", 0)
        vol_skills = volunteer.get("skills", [])
        vol_id = volunteer.get("id", "")
        vol_name = volunteer.get("name", "Unknown")

        # Calculate distances
        distance = haversine_distance(issue_lat, issue_lng, vol_lat, vol_lng)

        # Calculate scores
        skill_score = calculate_skill_match(vol_skills, issue_category)
        distance_score = calculate_distance_score(distance)

        # Combined score (60% skill, 40% distance)
        combined_score = (skill_score * 0.6) + (distance_score * 0.4)

        matches.append({
            "issue_id": issue.get("id", ""),
            "issue_description": issue.get("issue", ""),
            "volunteer_id": vol_id,
            "volunteer_name": vol_name,
            "match_score": round(combined_score, 2),
            "distance_km": round(distance, 2),
            "skill_score": round(skill_score, 2),
            "distance_score": round(distance_score, 2)
        })

    # Sort by combined score (highest first)
    matches.sort(key=lambda x: x["match_score"], reverse=True)

    return matches


def get_best_match(
    issue: Dict[str, Any],
    volunteers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Get the best matching volunteer for an issue.

    Args:
        issue: Issue data
        volunteers: List of volunteers

    Returns:
        Best match dictionary
    """
    matches = match_volunteers_to_issue(issue, volunteers)
    return matches[0] if matches else None
