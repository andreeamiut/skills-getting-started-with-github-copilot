"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    global activities
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    })
    yield


def test_root_redirect(client):
    """Test that root redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert len(data["Chess Club"]["participants"]) == 2


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    assert "Signed up test@mergington.edu for Chess Club" in response.json()["message"]
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    assert "test@mergington.edu" in activities_response.json()["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signup for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_duplicate_registration(client):
    """Test that a student cannot register twice for the same activity"""
    email = "michael@mergington.edu"
    response = client.post(
        f"/activities/Chess Club/signup?email={email}"
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_unregister_from_activity_success(client):
    """Test successful unregistration from an activity"""
    email = "michael@mergington.edu"
    response = client.delete(
        f"/activities/Chess Club/unregister?email={email}"
    )
    assert response.status_code == 200
    assert f"Unregistered {email} from Chess Club" in response.json()["message"]
    
    # Verify the participant was removed
    activities_response = client.get("/activities")
    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregister from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_not_registered_student(client):
    """Test unregistering a student who is not registered"""
    response = client.delete(
        "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]


def test_full_signup_unregister_flow(client):
    """Test complete flow: signup then unregister"""
    email = "newstudent@mergington.edu"
    activity = "Programming Class"
    
    # Sign up
    signup_response = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup_response.status_code == 200
    
    # Verify registration
    activities_response = client.get("/activities")
    assert email in activities_response.json()[activity]["participants"]
    
    # Unregister
    unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert unregister_response.status_code == 200
    
    # Verify unregistration
    final_response = client.get("/activities")
    assert email not in final_response.json()[activity]["participants"]
