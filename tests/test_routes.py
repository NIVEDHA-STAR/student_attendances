import pytest
import mongomock
from app import app, mongo
from datetime import datetime, timedelta

# ----------------------------
# Setup Flask test client
# ----------------------------
@pytest.fixture
def client(monkeypatch):
    # Mock MongoDB
    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr("app.mongo.db", mock_db)

    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

# ----------------------------
# Test home page
# ----------------------------
def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome" in response.data or b"index" in response.data

# ----------------------------
# Test professor signup
# ----------------------------
def test_professor_signup(client):
    response = client.post('/professor_signup', data={
        'name': 'Test Prof',
        'email': 'prof@example.com',
        'password': 'pass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"login" in response.data  # redirected to login

# ----------------------------
# Test professor login
# ----------------------------
def test_professor_login(client):
    # Add a professor manually
    mongo.db.professors.insert_one({
        'name': 'Test Prof',
        'email': 'prof@example.com',
        'password': 'pass123'
    })
    
    response = client.post('/professor_login', data={
        'email': 'prof@example.com',
        'password': 'pass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"dashboard" in response.data or b"professor" in response.data

# ----------------------------
# Test generate PIN
# ----------------------------
def test_generate_pin(client):
    # Login first
    with client.session_transaction() as sess:
        sess['professor'] = 'prof@example.com'
    
    response = client.get('/generate_pin')
    assert response.status_code == 200
    assert b"pin" in response.data.lower()

# ----------------------------
# Test student attendance
# ----------------------------
def test_student_attendance(client):
    # Insert a valid PIN
    mongo.db.pins.insert_one({
        'pin': 1234,
        'timestamp': datetime.utcnow(),
        'professor_email': 'prof@example.com'
    })

    response = client.post('/student_attendance', data={
        'name': 'Student One',
        'reg_no': 'REG123',
        'department': 'CSE',
        'year': '3',
        'subject_code': 'CS301',
        'pin': '1234'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"success" in response.data.lower() or b"marked" in response.data.lower()

# ----------------------------
# Test submit OD
# ----------------------------
def test_submit_od(client, tmp_path):
    # Create dummy certificate
    cert_file = tmp_path / "cert.pdf"
    cert_file.write_bytes(b"%PDF-1.4 dummy pdf content")
    
    response = client.post('/submit_od', data={
        'name': 'OD Student',
        'reg_no': 'OD001',
        'year': '2',
        'department': 'ECE',
        'od_date': '2025-08-23',
        'event_name': 'Seminar',
        'place': 'College',
        'certificate': (open(cert_file, 'rb'), 'cert.pdf')
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"od request" in response.data.lower()
