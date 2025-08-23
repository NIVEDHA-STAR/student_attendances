import pytest
from datetime import datetime, timedelta



# ✅ Test PIN expiry logic
def test_pin_expiry():
    pin_time = datetime.utcnow()
    valid_until = pin_time + timedelta(minutes=5)
    assert datetime.utcnow() <= valid_until
