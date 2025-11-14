import pytest


def test_root_redirect(client):
    """Test that GET / redirects to /static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test GET /activities returns all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    
    # Check that we have the expected activities
    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert "Math Team" in activities
    
    # Verify structure of an activity
    chess = activities["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess
    assert isinstance(chess["participants"], list)
    assert chess["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_signup_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "alice@mergington.edu"}
    )
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "alice@mergington.edu" in result["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "alice@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_duplicate(client):
    """Test signup fails when student is already registered"""
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 400
    result = response.json()
    assert "already signed up" in result["detail"]


def test_signup_activity_not_found(client):
    """Test signup fails when activity doesn't exist"""
    response = client.post(
        "/activities/NonExistent/signup",
        params={"email": "alice@mergington.edu"}
    )
    assert response.status_code == 404
    result = response.json()
    assert "Activity not found" in result["detail"]


def test_signup_activity_full(client):
    """Test signup fails when activity is full"""
    # Manually fill an activity to max capacity
    from src.app import activities
    activities["Chess Club"]["participants"] = [
        f"student{i}@mergington.edu" for i in range(12)  # max is 12
    ]
    
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "alice@mergington.edu"}
    )
    assert response.status_code == 400
    result = response.json()
    assert "full" in result["detail"]


def test_remove_participant_success(client):
    """Test successful removal of a participant"""
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 200
    result = response.json()
    assert "Removed" in result["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_remove_participant_not_found(client):
    """Test removal fails when participant doesn't exist in activity"""
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "nonexistent@mergington.edu"}
    )
    assert response.status_code == 404
    result = response.json()
    assert "not found" in result["detail"]


def test_remove_participant_activity_not_found(client):
    """Test removal fails when activity doesn't exist"""
    response = client.delete(
        "/activities/NonExistent/participants",
        params={"email": "michael@mergington.edu"}
    )
    assert response.status_code == 404
    result = response.json()
    assert "Activity not found" in result["detail"]


def test_signup_with_whitespace(client):
    """Test signup handles email with whitespace"""
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "  alice@mergington.edu  "}
    )
    assert response.status_code == 200
    
    # Try to signup again with different whitespace - should fail as duplicate
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "alice@mergington.edu"}
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_remove_participant_case_insensitive(client):
    """Test removal is case-insensitive for emails"""
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "MICHAEL@MERGINGTON.EDU"}
    )
    assert response.status_code == 200
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
