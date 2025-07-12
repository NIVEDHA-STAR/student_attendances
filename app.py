from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, send_from_directory
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
import random, pdfkit, calendar, os, certifi
from io import BytesIO
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from flask import make_response

# ✅ Step 1: Initialize the app
app = Flask(__name__)

# ✅ Step 2: Set secret key (AFTER creating the app)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

# ✅ Step 3: MongoDB configuration
app.config["MONGO_URI"] = "mongodb+srv://muthunivedha135:123nive@cluster0.er3xhxj.mongodb.net/student_attendance?retryWrites=true&w=majority&appName=Cluster0"


# ✅ Step 4: Initialize Mongo and Mail
mongo = PyMongo(app, tlsCAFile=certifi.where())
mail = Mail(app)



print("✅ Mongo Connected:", mongo.db)



# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'muthunivedha135@gmail.com'
app.config['MAIL_PASSWORD'] = '123@nivE'
app.config['MAIL_DEFAULT_SENDER'] = 'muthunivedha135@gmail.com'
mail = Mail(app)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/professor_signup', methods=['GET', 'POST'])
def professor_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        existing = mongo.db.professors.find_one({'email': email})
        if existing:
            return render_template('signup.html', error="Email already registered!")
        mongo.db.professors.insert_one({'name': name, 'email': email, 'password': password})
        return redirect(url_for('professor_login'))
    return render_template('signup.html')

@app.route('/check_mongo')
def check_mongo():
    return f"MONGO_URI: {app.config.get('MONGO_URI')}"


@app.route('/professor_login', methods=['GET', 'POST'])
def professor_login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        professor = mongo.db.professors.find_one({'email': email, 'password': password})
        if professor:
            session['professor'] = email
            return redirect(url_for('professor_dashboard'))
        else:
            error = "Invalid credentials!"
    return render_template('login.html', error=error)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        professor = mongo.db.professors.find_one({'email': email})
        if professor:
            mongo.db.professors.update_one({'email': email}, {'$set': {'password': new_password}})
            return redirect(url_for('professor_login'))
        else:
            return render_template('forgot_password.html', error="Email not found!")
    return render_template('forgot_password.html')

@app.route('/professor_dashboard')
def professor_dashboard():
    if 'professor' not in session:
        return redirect(url_for('professor_login'))
    od_requests = list(mongo.db.od_requests.find({'status': 'pending'}))
    return render_template('professor.html', od_requests=od_requests)

@app.route('/generate_pin')
def generate_pin():
    if 'professor' not in session:
        return redirect(url_for('professor_login'))

    pin = random.randint(1000, 9999)
    timestamp = datetime.utcnow()
    professor_email = session['professor']
    mongo.db.pins.insert_one({'pin': pin, 'timestamp': timestamp, 'professor_email': professor_email})

    valid_until = timestamp + timedelta(minutes=5)
    remaining_seconds = int((valid_until - datetime.utcnow()).total_seconds())

    return render_template('display_pin.html', pin=pin, valid_until=valid_until.strftime('%I:%M %p'), remaining_seconds=remaining_seconds)

@app.route('/student_attendance', methods=['GET', 'POST'])
def student_attendance():
    error = success = None
    if request.method == 'POST':
        name = request.form['name']
        reg_no = request.form['reg_no']
        department = request.form['department']
        year = str(request.form['year'])
        subject_code = request.form['subject_code']
        entered_pin = request.form['pin']
        ip_address = request.remote_addr

        latest_pin_doc = mongo.db.pins.find().sort('timestamp', -1).limit(1)
        pin_record = next(latest_pin_doc, None)

        if pin_record:
            valid_until = pin_record['timestamp'] + timedelta(minutes=5)
            if str(pin_record['pin']) == entered_pin and datetime.utcnow() <= valid_until:
                already_marked = mongo.db.attendance.find_one({
                    'used_pin': entered_pin,
                    '$or': [{'reg_no': reg_no}, {'ip_address': ip_address}]
                })
                if already_marked:
                    error = "❌ Attendance already submitted from this device or using this register number."
                else:
                    mongo.db.attendance.insert_one({
                        'name': name,
                        'reg_no': reg_no,
                        'department': department,
                        'year': year,
                        'subject_code': subject_code,
                        'timestamp': datetime.utcnow(),
                        'used_pin': entered_pin,
                        'ip_address': ip_address,
                        'professor_email': pin_record['professor_email'],
                        'hours_attended': 1
                    })
                    success = "✅ Attendance marked successfully!"
            else:
                error = "❌ Invalid or expired PIN!"
        else:
            error = "❌ No active PIN found!"
    return render_template('student.html', error=error, success=success)

@app.route('/certificates/<filename>')
def get_certificate(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Configurations for file upload
app.config['UPLOAD_FOLDER'] = 'uploads/certificates'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png'}

# Ensure that the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload_certificate', methods=['POST'])
def upload_certificate():
    if 'certificate' not in request.files:
        return 'No file part', 400

    certificate = request.files['certificate']

    if certificate and allowed_file(certificate.filename):
        filename = secure_filename(certificate.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        certificate.save(filepath)
        return f'Certificate uploaded successfully! Access it at /uploads/{filename}', 200
    else:
        return 'Invalid file type', 400

@app.route('/uploads/<filename>')
def upload_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/submit_od', methods=['POST'])
def submit_od():
    try:
        # Extract form data
        name = request.form.get('name')
        reg_no = request.form.get('reg_no')
        year = request.form.get('year')
        department = request.form.get('department')
        od_date = request.form.get('od_date')
        event_name = request.form.get('event_name')
        place = request.form.get('place')
        certificate = request.files.get('certificate')

        # Validate all required fields
        if not all([name, reg_no, year, department, od_date, event_name, place, certificate]):
            flash("⚠️ All OD fields and certificate are required!", "warning")
            return redirect(url_for('student_attendance'))

        # Validate certificate file
        if certificate and allowed_file(certificate.filename):
            filename = secure_filename(f"{reg_no}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{certificate.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            certificate.save(filepath)
        else:
            flash("⚠️ Invalid certificate file. Only PDF and image files are allowed.", "warning")
            return redirect(url_for('student_attendance'))

        # Validate and convert date
        try:
            od_date_obj = datetime.strptime(od_date, '%Y-%m-%d')
        except ValueError:
            flash("⚠️ Invalid OD date format. Use YYYY-MM-DD.", "warning")
            return redirect(url_for('student_attendance'))

        # Prepare data for MongoDB
        od_data = {
            'name': name,
            'reg_no': reg_no,
            'year': year,
            'department': department,
            'od_date': od_date_obj,
            'event_name': event_name,
            'place': place,
            'certificate_filename': filename,  # Save the certificate filename
            'status': 'pending',
            'submitted_at': datetime.utcnow()
        }

        # Insert OD request into MongoDB
        mongo.db.od_requests.insert_one(od_data)

        flash("✅ OD request submitted successfully.", "success")
        return redirect(url_for('student_attendance'))

    except Exception as e:
        flash(f"❌ Failed to submit OD request: {str(e)}", "danger")
        return redirect(url_for('student_attendance'))
@app.route('/approve_od', methods=['POST'])
def approve_od():
    try:
        od_id = request.form['od_id']
        od_data = mongo.db.od_requests.find_one({"_id": ObjectId(od_id)})

        if not od_data:
            flash("❌ OD request not found.", "danger")
            return redirect(url_for('professor_dashboard'))

        # Parse date to datetime object
        od_date = od_data.get('od_date')
        if isinstance(od_date, str):
            od_date = datetime.strptime(od_date, "%Y-%m-%d")
        elif not isinstance(od_date, datetime):
            od_date = datetime.utcnow()

        # Normalize timestamp to start of the day
        od_date = od_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Prepare attendance record for approved OD
        attendance_record = {
            "name": od_data.get('name'),
            "reg_no": od_data.get('reg_no'),
            "year": od_data.get('year'),
            "department": od_data.get('department'),
            "subject_code": "OD",  # Mark as OD attendance
            "timestamp": od_date,
            "event_name": od_data.get('event_name', ''),
            "place": od_data.get('place', ''),
            "certificate_filename": od_data.get('certificate_filename', None),
            "od": True,
            "status": "OD Present",
            "marked_by": "OD Approval",
            "marked_at": datetime.utcnow()
        }

        # Insert into attendance collection
        mongo.db.attendance.insert_one(attendance_record)

        # Update the OD request status to 'approved'
        mongo.db.od_requests.update_one(
            {"_id": ObjectId(od_id)},
            {"$set": {"status": "approved", "approval_date": datetime.utcnow()}}
        )

        flash("✅ OD request approved and reflected in Attendance Report.", "success")

    except Exception as e:
        flash(f"❌ Error approving OD request: {str(e)}", "danger")

    return redirect(url_for('professor_dashboard'))
# Update the route to reject the OD request
@app.route('/reject_od', methods=['POST'])
def reject_od():
    try:
        od_id = request.form['od_id']
        od_data = mongo.db.od_requests.find_one({"_id": ObjectId(od_id)})

        if not od_data:
            flash("❌ OD request not found.", "danger")
            return redirect(url_for('professor_dashboard'))

        # Update the OD request status to 'rejected'
        mongo.db.od_requests.update_one(
            {"_id": ObjectId(od_id)},
            {"$set": {"status": "rejected", "rejection_date": datetime.utcnow()}}
        )

        # Insert the rejected OD attendance into the normal attendance collection
        attendance_record = {
            "student_name": od_data["student_name"],
            "register_number": od_data.get("register_number"),
            "date": od_data["date"],
            "event_name": od_data.get("event_name", ""),
            "type": "od_rejected",
            "submitted_on": datetime.utcnow()
            # Add any other fields you want to store
        }
        mongo.db.attendance.insert_one(attendance_record)

        flash("🚫 OD request has been rejected and recorded in attendance.", "info")

    except Exception as e:
        flash(f"❌ Error rejecting OD request: {str(e)}", "danger")

    return redirect(url_for('professor_dashboard'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        flash("❌ Certificate file not found.", "danger")
        return redirect(url_for('professor_dashboard'))


@app.route('/monthly_report', methods=['GET', 'POST'])
def monthly_report():
    data = []
    department = year = month_str = None

    if request.method == 'POST':
        department = request.form['department']
        year = request.form['year']
        month_str = request.form['month']

        year_val, month_val = map(int, month_str.split('-'))
        start_date = datetime(year_val, month_val, 1)
        end_date = datetime(year_val, month_val, calendar.monthrange(year_val, month_val)[1], 23, 59, 59)

        pipeline = [
            {"$match": {
                "department": department,
                "year": year,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": {
                    "reg_no": "$reg_no",
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
                },
                "total_hours": {"$sum": "$hours_attended"}
            }},
            {"$group": {
                "_id": "$_id.reg_no",
                "days_present": {"$sum": 1},
                "total_hours": {"$sum": "$total_hours"}
            }},
            {"$project": {
                "reg_no": "$_id",
                "attendance_percent": {
                    "$round": [{"$multiply": [{"$divide": ["$total_hours", 7]}, 3]}, 2]
                },
                "_id": 0
            }}
        ]

        result = list(mongo.db.attendance.aggregate(pipeline))
        data = result


    # This should always be the final return (not indented under the POST block)
    return render_template('monthly_report.html', data=data, department=department, year=year, month=month_str)


@app.route('/attendance_report', methods=['GET', 'POST'])
def attendance_report():
    if 'professor' not in session:
        return redirect(url_for('professor_login'))

    professor_email = session['professor']
    selected_date = request.args.get('date')
    selected_department = request.args.get('department')
    selected_year = request.args.get('year')

    # === Main attendance filter ===
    query = {'professor_email': professor_email}
    if selected_department and selected_department != 'All':
        query['department'] = selected_department
    if selected_year and selected_year != 'All':
        query['year'] = selected_year
    if selected_date:
        try:
            # Convert the selected date to datetime object
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
            start = datetime(date_obj.year, date_obj.month, date_obj.day)
            end = start + timedelta(days=1)
            query['timestamp'] = {'$gte': start, '$lt': end}
        except ValueError:
            flash("Invalid date format", "warning")
            selected_date = None

    # Fetch attendance records based on the filter
    records = list(mongo.db.attendance.find(query))

    # === OD Filters (no professor_email) ===
    od_filter = {}
    if selected_department and selected_department != 'All':
        od_filter['department'] = selected_department
    if selected_year and selected_year != 'All':
        od_filter['year'] = selected_year
    if selected_date:
        # Use the `od_date` to filter pending OD requests based on the selected date
        try:
            # Convert selected date to datetime to filter OD requests
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
            start = datetime(date_obj.year, date_obj.month, date_obj.day)
            end = start + timedelta(days=1)
            od_filter['od_date'] = {'$gte': start, '$lt': end}
        except ValueError:
            flash("Invalid date format for OD", "warning")
            selected_date = None

    # Get Pending OD Requests
    od_requests = list(mongo.db.od_requests.find({**od_filter, 'status': 'pending'}))

    # Get Approved OD and add as attendance
    approved_od = list(mongo.db.od_requests.find({**od_filter, 'status': 'approved'}))
    for od in approved_od:
        try:
            # Ensure od_date is in datetime format
            timestamp = datetime.strptime(od.get("od_date", ""), "%Y-%m-%d")
        except Exception:
            timestamp = datetime.now()  # Default timestamp in case of parsing error
        records.append({
            "name": od.get("name"),
            "reg_no": od.get("reg_no"),
            "department": od.get("department"),
            "year": od.get("year"),
            "subject_code": "OD",
            "timestamp": timestamp,
            "od": True  # Mark as OD attendance
        })

    # Sort all records by timestamp in descending order
    records.sort(key=lambda r: r['timestamp'], reverse=True)

    # Return rendered template with filtered records
    return render_template(
        'attendance_report.html',
        records=records,
        od_requests=od_requests,
        selected_date=selected_date,
        selected_department=selected_department,
        selected_year=selected_year
    )



@app.route('/download_pdf')
def download_pdf():
    if 'professor' not in session:
        return redirect(url_for('professor_login'))

    professor_email = session['professor']
    query = {'professor_email': professor_email}

    selected_date = request.args.get('date')
    selected_department = request.args.get('department')
    selected_year = request.args.get('year')

    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
            start = datetime(date_obj.year, date_obj.month, date_obj.day)
            end = start + timedelta(days=1)
            query['timestamp'] = {'$gte': start, '$lt': end}
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.")
            return redirect(url_for('attendance_report'))

    if selected_department:
        query['department'] = selected_department
    if selected_year:
        query['year'] = str(selected_year)

    records = list(mongo.db.attendance.find(query))
    rendered = render_template('professor_pdf.html', records=records, professor_email=professor_email)

    # Create PDF with pdfkit
    pdf = pdfkit.from_string(rendered, False)

    return send_file(BytesIO(pdf), download_name='attendance_report.pdf', as_attachment=True, mimetype='application/pdf')



@app.route('/download_monthly_report', methods=['POST'])
def download_monthly_report():
    department = request.form['department']
    year = request.form['year']
    month = request.form['month']
    data = []  # You need to fetch or calculate this data
    current_date = datetime.now().strftime("%Y-%m-%d")

    rendered_html = render_template('monthly_report_pdf.html', 
                                    department=department,
                                    year=year,
                                    month=month,
                                    data=data,
                                    current_date=current_date)

    pdf = pdfkit.from_string(rendered_html, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Monthly_Report_{month}.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True)
