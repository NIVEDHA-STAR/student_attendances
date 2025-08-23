# tests/test_functional.py
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_generate_pin_route(client):
    response = client.post('/generate_pin', data={'pin': '1234'})
    assert response.status_code == 200
    assert b'PIN generated' in response.data

def test_student_attendance(client):
    # Submit attendance with valid PIN
    response = client.post('/submit_attendance', data={'pin': '1234', 'name': 'John', 'reg_no': '101'})
    assert response.status_code == 200
    assert b'Attendance marked' in response.data

def test_pdf_report_route(client):
    response = client.get('/download_report')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
