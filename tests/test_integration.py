# tests/test_integration.py
import pytest
from app import app, mongo  # Make sure 'mongo' is your PyMongo object

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_attendance_flow(client):
    # Professor generates PIN
    client.post('/generate_pin', data={'pin': '5678'})

    # Student submits attendance
    client.post('/submit_attendance', data={'pin': '5678', 'name': 'Alice', 'reg_no': '102'})

    # Check MongoDB for record
    record = mongo.db.attendance.find_one({'reg_no': '102'})
    assert record is not None
    assert record['name'] == 'Alice'

    # Generate PDF
    response = client.get('/download_report')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
