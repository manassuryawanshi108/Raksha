"""Sample NGO datasets for testing and demonstration."""

from typing import List, Dict, Any

# Sample NGO issues representing various humanitarian needs
SAMPLE_ISSUES = [
    {
        "location": "Village A, Rural District",
        "issue": "No clean water for 100 people. The only well is contaminated.",
        "people_count": 100,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "contact_info": "village.a@ngo.org"
    },
    {
        "location": "Refugee Camp Sector 3",
        "issue": "Food shortage critical. 500 families running out of rations.",
        "people_count": 2500,
        "latitude": 28.5355,
        "longitude": 77.3910,
        "contact_info": "sector3@refugeecamp.org"
    },
    {
        "location": "Mountain Community B",
        "issue": "No doctor or medical clinic. Elderly patients need immediate care.",
        "people_count": 75,
        "latitude": 30.0668,
        "longitude": 79.0193,
        "contact_info": "community.b@mountain.org"
    },
    {
        "location": "Coastal Area C",
        "issue": "Homes destroyed by flood. Families need emergency shelter.",
        "people_count": 300,
        "latitude": 19.0760,
        "longitude": 72.8777,
        "contact_info": "area.c@coastal.org"
    },
    {
        "location": "Urban Slum D",
        "issue": "Children have no access to school. Need books and teachers.",
        "people_count": 150,
        "latitude": 18.9388,
        "longitude": 72.8354,
        "contact_info": "slum.d@urban.org"
    },
    {
        "location": "Desert Region E",
        "issue": "Severe drought. No water for drinking or agriculture. Emergency situation.",
        "people_count": 800,
        "latitude": 26.9124,
        "longitude": 75.7873,
        "contact_info": "region.e@desert.org"
    },
    {
        "location": "Forest Village F",
        "issue": "Malnutrition among children. Need food and nutrition support.",
        "people_count": 200,
        "latitude": 21.1458,
        "longitude": 79.0882,
        "contact_info": "village.f@forest.org"
    },
    {
        "location": "Industrial Area G",
        "issue": "Water contamination from factory. People getting sick.",
        "people_count": 450,
        "latitude": 23.0225,
        "longitude": 72.5714,
        "contact_info": "area.g@industrial.org"
    },
    {
        "location": "Remote Island H",
        "issue": "No medical supplies. Pregnant women need healthcare urgently.",
        "people_count": 60,
        "latitude": 11.9416,
        "longitude": 92.7499,
        "contact_info": "island.h@remote.org"
    },
    {
        "location": "Border Town I",
        "issue": "Displaced families need temporary housing and food rations.",
        "people_count": 600,
        "latitude": 31.6340,
        "longitude": 74.8723,
        "contact_info": "town.i@border.org"
    },
    {
        "location": "Valley Community J",
        "issue": "Crop failure due to pests. Farmers facing hunger and starvation.",
        "people_count": 350,
        "latitude": 32.2432,
        "longitude": 77.1892,
        "contact_info": "community.j@valley.org"
    },
    {
        "location": "City Slum K",
        "issue": "Contaminated water causing disease outbreak. Children dying.",
        "people_count": 1000,
        "latitude": 22.5726,
        "longitude": 88.3639,
        "contact_info": "slum.k@city.org"
    }
]

# Sample volunteers with various skills
SAMPLE_VOLUNTEERS = [
    {
        "name": "Rajesh Kumar",
        "skills": ["plumbing", "water treatment", "construction"],
        "latitude": 28.6139,
        "longitude": 77.2090,
        "phone": "+91-9876543210",
        "email": "rajesh@volunteer.org",
        "status": "available"
    },
    {
        "name": "Priya Sharma",
        "skills": ["medical", "nursing", "first aid"],
        "latitude": 28.5355,
        "longitude": 77.3910,
        "phone": "+91-9876543211",
        "email": "priya@volunteer.org",
        "status": "available"
    },
    {
        "name": "Mohammed Ali",
        "skills": ["cooking", "food distribution", "logistics"],
        "latitude": 19.0760,
        "longitude": 72.8777,
        "phone": "+91-9876543212",
        "email": "ali@volunteer.org",
        "status": "available"
    },
    {
        "name": "Sunita Devi",
        "skills": ["teaching", "education", "childcare"],
        "latitude": 18.9388,
        "longitude": 72.8354,
        "phone": "+91-9876543213",
        "email": "sunita@volunteer.org",
        "status": "available"
    },
    {
        "name": "Arun Patel",
        "skills": ["construction", "carpentry", "engineering"],
        "latitude": 26.9124,
        "longitude": 75.7873,
        "phone": "+91-9876543214",
        "email": "arun@volunteer.org",
        "status": "available"
    },
    {
        "name": "Dr. Meera Reddy",
        "skills": ["doctor", "medical", "surgery", "diagnosis"],
        "latitude": 21.1458,
        "longitude": 79.0882,
        "phone": "+91-9876543215",
        "email": "meera@volunteer.org",
        "status": "available"
    },
    {
        "name": "Vikram Singh",
        "skills": ["agriculture", "farming", "logistics"],
        "latitude": 23.0225,
        "longitude": 72.5714,
        "phone": "+91-9876543216",
        "email": "vikram@volunteer.org",
        "status": "available"
    },
    {
        "name": "Anita Gupta",
        "skills": ["nutrition", "cooking", "healthcare"],
        "latitude": 11.9416,
        "longitude": 92.7499,
        "phone": "+91-9876543217",
        "email": "anita@volunteer.org",
        "status": "available"
    }
]


def get_sample_issues() -> List[Dict[str, Any]]:
    """Return sample issues for testing."""
    return SAMPLE_ISSUES


def get_sample_volunteers() -> List[Dict[str, Any]]:
    """Return sample volunteers for testing."""
    return SAMPLE_VOLUNTEERS


def seed_database(db) -> Dict[str, Any]:
    """
    Seed the database with sample data.

    Args:
        db: Firebase database instance

    Returns:
        Summary of seeded data
    """
    issue_ids = db.batch_add_issues(SAMPLE_ISSUES)
    volunteer_ids = []

    for volunteer in SAMPLE_VOLUNTEERS:
        vol_id = db.add_volunteer(volunteer)
        volunteer_ids.append(vol_id)

    return {
        "issues_added": len(issue_ids),
        "volunteers_added": len(volunteer_ids),
        "issue_ids": issue_ids,
        "volunteer_ids": volunteer_ids
    }
