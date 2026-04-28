"""AI service for issue classification and urgency scoring."""

from typing import Dict, Any, Tuple
from models.schema import IssueCategory, PriorityLevel


# Keyword-based classification mappings
CATEGORY_KEYWORDS = {
    IssueCategory.WATER: [
        "water", "drink", "well", "pipe", "tap", "bottle", "contaminated",
        "purify", "hydration", "drought", "thirst", "aquifer", "reservoir"
    ],
    IssueCategory.FOOD: [
        "food", "hungry", "meal", "eat", "hunger", "starve", "nutrition",
        "famine", "crop", "harvest", "ration", "kitchen", "grain", "bread"
    ],
    IssueCategory.HEALTHCARE: [
        "doctor", "medicine", "hospital", "sick", "disease", "clinic",
        "patient", "treatment", "vaccine", "injury", "health", "medical",
        "symptom", "diagnosis", "surgery", "pharmacy", "nurse"
    ],
    IssueCategory.SHELTER: [
        "shelter", "home", "house", "roof", "housing", "refugee", "displaced",
        "tent", "evacuation", "homeless", "accommodation", "residence"
    ],
    IssueCategory.EDUCATION: [
        "school", "education", "teacher", "student", "learn", "book",
        "classroom", "literacy", "curriculum", "training", "skills"
    ]
}

# Urgency multipliers for keywords (higher = more urgent)
URGENCY_KEYWORDS = {
    # Immediate crisis
    "emergency": 1.0, "critical": 0.95, "dying": 1.0, "death": 0.95,
    "urgent": 0.9, "desperate": 0.9, "poisoned": 0.9, "immediate": 0.85,
    # Natural disasters
    "flood": 0.85, "flooded": 0.85, "flooding": 0.85, "earthquake": 0.9,
    "cyclone": 0.9, "typhoon": 0.9, "landslide": 0.88, "tsunami": 0.95,
    "fire": 0.85, "wildfire": 0.9, "collapse": 0.88, "collapsed": 0.88,
    "disaster": 0.85, "storm": 0.8, "drought": 0.8, "explosion": 0.9,
    # Deprivation
    "no": 0.75, "lack": 0.7, "shortage": 0.75, "scarcity": 0.7,
    "running out": 0.85, "severe": 0.85, "contaminated": 0.85,
    "no water": 0.85, "no food": 0.85, "starving": 0.9, "hunger": 0.8,
    "disease": 0.85, "epidemic": 0.9, "outbreak": 0.88, "infected": 0.85,
    # Vulnerable populations
    "children": 0.8, "child": 0.8, "infant": 0.85, "baby": 0.85,
    "elderly": 0.75, "pregnant": 0.85, "disabled": 0.8, "injured": 0.82,
    "trapped": 0.9, "missing": 0.85, "stranded": 0.85, "homeless": 0.75,
    "displaced": 0.75, "refugee": 0.75, "malnutrition": 0.85,
}


def classify_issue(issue_text: str) -> str:
    """
    Classify issue text into a category using keyword matching.

    Args:
        issue_text: Description of the issue

    Returns:
        Category name as string
    """
    issue_lower = issue_text.lower()

    # Count keyword matches for each category
    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in issue_lower)
        category_scores[category] = score

    # Return category with highest score
    if max(category_scores.values()) == 0:
        return IssueCategory.OTHER.value

    best_category = max(category_scores, key=category_scores.get)
    return best_category.value


def calculate_urgency(issue_text: str, people_count: int) -> float:
    """
    Calculate urgency score (0-1) based on keywords and people count.

    Args:
        issue_text: Description of the issue
        people_count: Number of people affected

    Returns:
        Urgency score between 0 and 1
    """
    issue_lower = issue_text.lower()

    # Base urgency from keywords
    keyword_urgency = 0.0
    for keyword, weight in URGENCY_KEYWORDS.items():
        if keyword in issue_lower:
            keyword_urgency = max(keyword_urgency, weight)

    # People count factor (logarithmic scaling)
    # 10 people -> 0.3, 100 people -> 0.6, 1000+ people -> 0.9
    import math
    people_factor = min(0.9, math.log10(max(1, people_count)) / 3.5)

    # Combine factors (weighted average)
    urgency = (keyword_urgency * 0.6) + (people_factor * 0.4)

    return round(min(1.0, max(0.0, urgency)), 2)


def get_priority_level(urgency_score: float) -> str:
    """
    Convert urgency score to priority level.

    Args:
        urgency_score: Score between 0 and 1

    Returns:
        Priority level string
    """
    if urgency_score >= 0.7:
        return PriorityLevel.HIGH.value
    elif urgency_score >= 0.4:
        return PriorityLevel.MEDIUM.value
    else:
        return PriorityLevel.LOW.value


def process_issue(issue_text: str, people_count: int) -> Dict[str, Any]:
    """
    Process an issue and return classification results.

    Args:
        issue_text: Description of the issue
        people_count: Number of people affected

    Returns:
        Dictionary with category, urgency, and priority
    """
    category = classify_issue(issue_text)
    urgency = calculate_urgency(issue_text, people_count)
    priority = get_priority_level(urgency)

    return {
        "category": category,
        "urgency": urgency,
        "priority": priority
    }
