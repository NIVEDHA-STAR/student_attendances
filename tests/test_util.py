import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app import app, allowed_file   # main app.py file la irundhu import

# ---- Flask test client fixture ----
@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_allowed_file_invalid_extensions():
    assert allowed_file("malware.exe") is False
    assert allowed_file("notes.txt") is False
    assert allowed_file("attendance.csv") is False
    assert allowed_file("no_extension") is False

# ---- Student attendance invalid PIN ----
# ---- Student attendance missing fields ----
def test_student_attendance_missing_fields(client):
    response = client.post("/student_attendance", data={
        "name": "Test",
        # reg_no missing
        "department": "CSE",
        "year": "3",
        "subject_code": "CS101",
        "pin": "1234"
    })
    assert response.status_code == 400 or b"Missing" in response.data

# ---- Professor dashboard access without login ----
def test_prof_dashboard_without_login(client):
    response = client.get("/professor_dashboard", follow_redirects=False)
    assert response.status_code == 302   # Redirect to login

