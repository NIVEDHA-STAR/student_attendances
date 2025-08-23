import pytest
import mongomock
from datetime import datetime, timedelta
from core import is_pin_valid, mark_attendance, approve_od

# Mock MongoDB
@pytest.fixture
def mock_db(monkeypatch):
    db = mongomock.MongoClient().db
    monkeypatch.setattr("core.mongo.db", db)
    return db

# ----------------------------
# Test PIN validation
# ----------------------------
def test_is_pin_valid_success(mock_db):
    # Insert a valid PIN
    mock_db.pins.insert_one({
        'pin': 1234,
        'timestamp': datetime.utcnow()
    })
    assert is_pin_valid(1234) == True

def test_is_pin_valid_expired(mock_db):
    # Insert an expired PIN (older than 5 minutes)
    mock_db.pins.insert_one({
        'pin': 5678,
        'timestamp': datetime.utcnow() - timedelta(minutes=10)
    })
    assert is_pin_valid(5678) == False

def test_is_pin_valid_wrong(mock_db):
    mock_db.pins.insert_one({
        'pin': 1111,
        'timestamp': datetime.utcnow()
    })
    assert is_pin_valid(2222) == False

# ----------------------------
# Test attendance marking
# ----------------------------
def test_mark_attendance_success(mock_db):
    # Insert a valid PIN
    mock_db.pins.insert_one({
        'pin': 9999,
        'timestamp': datetime.utcnow(),
        'professor_email': 'prof@example.com'
    })
    
    student_data = {
        'name': 'Test Student',
        'reg_no': 'REG123',
        'department': 'CSE',
        'year': '3',
        'subject_code': 'CS301',
        'ip_address': '127.0.0.1'
    }
    
    result = mark_attendance(student_data, 9999)
    assert result['success'] == True
    assert mock_db.attendance.count_documents({}) == 1

def test_mark_attendance_already_marked(mock_db):
    mock_db.pins.insert_one({
        'pin': 8888,
        'timestamp': datetime.utcnow(),
        'professor_email': 'prof@example.com'
    })
    
    # Already marked attendance
    mock_db.attendance.insert_one({
        'reg_no': 'REG123',
        'used_pin': 8888,
        'ip_address': '127.0.0.1'
    })
    
    student_data = {
        'name': 'Test Student',
        'reg_no': 'REG123',
        'department': 'CSE',
        'year': '3',
        'subject_code': 'CS301',
        'ip_address': '127.0.0.1'
    }
    
    result = mark_attendance(student_data, 8888)
    assert result['success'] == False
    assert "already submitted" in result['error']

# ----------------------------
# Test OD approval
# ----------------------------
def test_approve_od_success(mock_db):
    # Insert OD request
    od_id = mock_db.od_requests.insert_one({
        'name': 'OD Student',
        'reg_no': 'OD123',
        'year': '2',
        'department': 'ECE',
        'od_date': datetime.utcnow(),
        'event_name': 'Seminar',
        'place': 'College',
        'certificate_filename': 'cert.pdf',
        'status': 'pending'
    }).inserted_id
    
    result = approve_od(str(od_id))
    assert result['success'] == True
    
    # Check attendance collection
    attendance_records = list(mock_db.attendance.find({'reg_no': 'OD123'}))
    assert len(attendance_records) == 1
