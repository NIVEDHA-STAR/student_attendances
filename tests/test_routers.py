import pytest
from app import app
from datetime import datetime
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# ✅ Test home page
def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome" in response.data or b"Home" in response.data

# ✅ Test professor login GET
def test_professor_login_get(client):
    response = client.get('/professor_login')
    assert response.status_code == 200
    assert b"Login" in response.data

# 