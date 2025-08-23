# core_logic.py
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------- PIN VALIDATION -------------------
def validate_pin(mongo, entered_pin):
    """Check if a PIN exists and is still valid (5 minutes)."""
    latest_pin_doc = mongo.db.pins.find().sort('timestamp', -1).limit(1)
    pin_record = next(latest_pin_doc, None)
    if pin_record:
        valid_until = pin_record['timestamp'] + timedelta(minutes=5)
        if str(pin_record['pin']) == str(entered_pin) and datetime.utcnow() <= valid_until:
            return True, pin_record
    return False, None

# ------------------- ATTENDANCE INSERTION -------------------
def mark_attendance(mongo, student_data, entered_pin, ip_address):
    """Insert student attendance if PIN valid and not already marked."""
    is_valid, pin_record = validate_pin(mongo, entered_pin)
    if not is_valid:
        return False, "❌ Invalid or expired PIN!"
    
    # Check if already marked
    already_marked = mongo.db.attendance.find_one({
        'used_pin': entered_pin,
        '$or': [{'reg_no': student_data['reg_no']}, {'ip_address': ip_address}]
    })
    if already_marked:
        return False, "❌ Attendance already submitted from this device or using this register number."

    attendance_record = {
        'name': student_data['name'],
        'reg_no': student_data['reg_no'],
        'department': student_data['department'],
        'year': student_data['year'],
        'subject_code': student_data['subject_code'],
        'timestamp': datetime.utcnow(),
        'used_pin': entered_pin,
        'ip_address': ip_address,
        'professor_email': pin_record['professor_email'],
        'hours_attended': 1
    }
    mongo.db.attendance.insert_one(attendance_record)
    return True, "✅ Attendance marked successfully!"

# ------------------- OD REQUEST SUBMISSION -------------------
def submit_od_request(mongo, od_data, certificate_filename):
    """Submit an OD request to MongoDB."""
    od_data_record = {
        'name': od_data['name'],
        'reg_no': od_data['reg_no'],
        'year': od_data['year'],
        'department': od_data['department'],
        'od_date': od_data['od_date'],
        'event_name': od_data['event_name'],
        'place': od_data['place'],
        'certificate_filename': certificate_filename,
        'status': 'pending',
        'submitted_at': datetime.utcnow()
    }
    mongo.db.od_requests.insert_one(od_data_record)
    return True

# ------------------- OD APPROVAL -------------------
def approve_od_request(mongo, od_id):
    od_data = mongo.db.od_requests.find_one({"_id": ObjectId(od_id)})
    if not od_data:
        return False, "❌ OD request not found."
    
    # Normalize date
    od_date = od_data.get('od_date')
    if isinstance(od_date, str):
        od_date = datetime.strptime(od_date, "%Y-%m-%d")
    elif not isinstance(od_date, datetime):
        od_date = datetime.utcnow()
    od_date = od_date.replace(hour=0, minute=0, second=0, microsecond=0)

    attendance_record = {
        "name": od_data.get('name'),
        "reg_no": od_data.get('reg_no'),
        "year": od_data.get('year'),
        "department": od_data.get('department'),
        "subject_code": "OD",
        "timestamp": od_date,
        "event_name": od_data.get('event_name', ''),
        "place": od_data.get('place', ''),
        "certificate_filename": od_data.get('certificate_filename', None),
        "od": True,
        "status": "OD Present",
        "marked_by": "OD Approval",
        "marked_at": datetime.utcnow()
    }
    mongo.db.attendance.insert_one(attendance_record)
    mongo.db.od_requests.update_one(
        {"_id": ObjectId(od_id)},
        {"$set": {"status": "approved", "approval_date": datetime.utcnow()}}
    )
    return True, "✅ OD request approved and reflected in Attendance Report."

# ------------------- OD REJECTION -------------------
def reject_od_request(mongo, od_id):
    od_data = mongo.db.od_requests.find_one({"_id": ObjectId(od_id)})
    if not od_data:
        return False, "❌ OD request not found."

    mongo.db.od_requests.update_one(
        {"_id": ObjectId(od_id)},
        {"$set": {"status": "rejected", "rejection_date": datetime.utcnow()}}
    )

    attendance_record = {
        "student_name": od_data.get("name"),
        "register_number": od_data.get("reg_no"),
        "date": od_data.get("od_date"),
        "event_name": od_data.get("event_name", ""),
        "type": "od_rejected",
        "submitted_on": datetime.utcnow()
    }
    mongo.db.attendance.insert_one(attendance_record)
    return True, "🚫 OD request has been rejected and recorded in attendance."
