import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_get_activities_returns_activity_details_and_participants():
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert activities["Chess Club"]["description"]
    assert activities["Chess Club"]["schedule"]
    assert isinstance(activities["Chess Club"]["participants"], list)


def test_signup_adds_participant():
    email = "new.student@mergington.edu"

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant():
    email = "new.student@mergington.edu"
    signup_url = "/activities/Chess%20Club/signup"
    signup_response = client.post(signup_url, params={"email": email})
    assert signup_response.status_code == 200

    response = client.post(signup_url, params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities["Chess Club"]["participants"].count(email) == 1


def test_unregister_removes_participant():
    email = "michael@mergington.edu"

    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_rejects_unregistered_participant():
    email = "not.registered@example.com"

    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert email not in app_module.activities["Chess Club"]["participants"]


@pytest.mark.parametrize("method", ["post", "delete"])
def test_signup_and_unregister_reject_unknown_activity(method):
    response = getattr(client, method)(
        "/activities/Unknown%20Club/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"