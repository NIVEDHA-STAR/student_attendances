# tests/test_unit.py
import pytest
from datetime import datetime, timedelta
from app import generate_pin, is_pin_valid  # Make sure these functions exist

def test_generate_pin_length():
    pin = generate_pin()
    assert len(str(pin)) == 4
    assert pin.isdigit()  # PIN should only contain digits

def test_pin_expiry():
    # expired PIN
    old_time = datetime.now() - timedelta(minutes=6)
    assert is_pin_valid(old_time) == False

    # valid PIN
    recent_time = datetime.now() - timedelta(minutes=4)
    assert is_pin_valid(recent_time) == True
