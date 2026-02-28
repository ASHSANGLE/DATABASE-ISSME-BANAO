import os
from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime
from modals import User, create_guardian, create_patient, create_notification, create_unity_user, create_appointment
import google.generativeai as genai

# 1. Setup and Configurations
load_dotenv()
app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or "a_very_secret_key"
app.config['MONGO_URI'] = os.getenv('MONGO_URI') or "mongodb://localhost:27017/seniorcare"
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    _gmodel = genai.GenerativeModel('gemini-1.5-flash', generation_config=genai.types.GenerationConfig(temperature=0.4, max_output_tokens=350))
else:
    _gmodel = None

# Initialize MongoDB
mongo = PyMongo(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_id(mongo, user_id)

# Create upload folder if missing
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Serve assets
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

# --- ROUTES START HERE ---

@app.route('/')
def index():
    return render_template('front.html')

@app.route('/main')
def main_page():
    return render_template('Main-page.html')

@app.route('/signup')
def signup_page():
    return render_template('signupcommon.html')

@app.route('/get-started')
def get_started():
    return render_template('get-started.html')

@app.route('/connection')
@login_required
def connection():
    return render_template('connection.html')

@app.route('/unityhub/auth')
def unityhub_auth():
    return render_template('stu-ngo-login.html')

@app.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect(url_for('index'))

# --- GUARDIAN AUTH ---

@app.route('/signup/guardian', methods=['GET', 'POST'])
def signup_guardian():
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
           
            # Check if user already exists
            if mongo.db.guardians.find_one({'email': email}):
                return "Email already registered", 400
               
            # Create Guardian
            result = create_guardian(mongo, email, password)
           
            # Login
            user_data = mongo.db.guardians.find_one({'_id': result.inserted_id})
            user = User(user_data, 'guardian')
            login_user(user)
           
            return redirect('/guardian-dashboard')
           
        return render_template('create-user.html')
    except Exception as e:
        print(f"Error in signup_guardian: {e}")
        return f"An error occurred: {str(e)}", 500

@app.route('/login/guardian', methods=['GET', 'POST'])
def login():
    # This serves as the main login for Guardians
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
           
            user_data = mongo.db.guardians.find_one({'email': email})
           
            if user_data and check_password_hash(user_data['password'], password):
                user = User(user_data, 'guardian')
                login_user(user)
                return redirect('/guardian-dashboard')
               
            return "Invalid credentials", 401
        return render_template('gardianlogin.html')
    except Exception as e:
        print(f"Error in login: {e}")
        return f"Login failed: {str(e)}", 500

# To support the legacy /login route redirection
@app.route('/login')
def login_redirect():
    return render_template('logincommon.html')


# --- PATIENT AUTH ---

@app.route('/signup/patient')
def patient_signup_page():
    return render_template('patient-signup.html')

@app.route('/signup-patient', methods=['POST'])
@login_required
def signup_patient():
    # Only a logged-in Guardian can register a patient?
    # Or is this public? The previous code checked for session['guardian_id'],
    # implying the Guardian must be logged in to add a patient.
    try:
        if current_user.role != 'guardian':
             return "Unauthorized", 403

        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')

        if not all([name, email, password]):
             return "Missing required fields", 400

        # Create Patient
        create_patient(mongo, name, email, password, phone, current_user.id)
       
        return redirect('/guardian-dashboard')
    except Exception as e:
        print(f"Error in signup_patient: {e}")
        return f"Signup failed: {str(e)}", 500

@app.route('/login/patient', methods=['GET', 'POST'])
def patient_login():
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
           
            user_data = mongo.db.patients.find_one({'email': email})
           
            if user_data and check_password_hash(user_data['password'], password):
                user = User(user_data, 'patient')
                login_user(user)
                return redirect('/patient-dashboard')
               
            return "Invalid credentials", 401
        return render_template('patient-login.html')
    except Exception as e:
        print(f"Error in patient login: {e}")
        return f"Login failed: {str(e)}", 500

# --- DASHBOARDS ---

@app.route('/guardian-dashboard')
@login_required
def dashboard():
    try:
        if current_user.role != 'guardian':
            return redirect('/patient-dashboard')
           
        # Fetch patients link to this guardian
        # Important: current_user.id is a string (because of User class), MongoDB stores guardian_id as string if we did it right in create_patient
        patients = list(mongo.db.patients.find({'guardian_id': current_user.id}))
        return render_template('guardian-dashboard.html', patients=patients)
    except Exception as e:
        return f"Dashboard error: {str(e)}", 500

@app.route('/patient-dashboard')
@login_required
def patient_dashboard():
    try:
        if current_user.role != 'patient':
            return redirect('/guardian-dashboard')
           
        # We can pass the patient object, though the template might not use it yet
        return render_template('patient-dashboard.html', patient=current_user)
    except Exception as e:
         return f"Dashboard error: {str(e)}", 500


# --- FEATURES ---

@app.route('/notifications')
@login_required
def notifications():
    try:
        # Fetch notifications for current user
        feed = list(mongo.db.notifications.find({'user_id': current_user.id}).sort('timestamp', -1))
        return render_template('notifications.html', feed=feed)
    except Exception as e:
        return f"Notification error: {str(e)}", 500

@app.route('/trigger-refill/<patient_id>', methods=['POST'])
def trigger_refill(patient_id):
    try:
        # Verify patient exists
        patient = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
           
        medicine_name = request.form.get('medicine_name', 'Medication')
       
        guardian_id = patient.get('guardian_id')
        if guardian_id:
             create_notification(mongo, guardian_id, f"Refill requested for {medicine_name} by {patient['name']}")
       
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/trigger-sos/<patient_id>', methods=['POST'])
def trigger_sos(patient_id):
    try:
        patient = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
        if not patient:
            return jsonify({"status": "error", "message": "Patient not found"}), 404
           
        # Update emergency status
        mongo.db.patients.update_one({'_id': ObjectId(patient_id)}, {'$set': {'is_emergency': True}})
       
        guardian_id = patient.get('guardian_id')
        if guardian_id:
            create_notification(mongo, guardian_id, f"🚨 EMERGENCY: {patient.get('name')} needs help!")
       
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/check-emergency')
@login_required
def check_emergency():
    try:
        if current_user.role == 'guardian':
             # Find any patient of this guardian with is_emergency=True
            emergency = mongo.db.patients.find_one({'guardian_id': current_user.id, 'is_emergency': True})
            if emergency:
                return jsonify({"emergency_detected": True, "patient_name": emergency['name']})
        return jsonify({"emergency_detected": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload-record/<patient_id>', methods=['POST'])
@login_required
def upload_record(patient_id):
    try:
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
           
            mongo.db.patients.update_one({'_id': ObjectId(patient_id)}, {'$set': {'medical_records': filename}})
            return redirect('/guardian-dashboard')
        return "Invalid file", 400
    except Exception as e:
        return f"Upload error: {str(e)}", 500

@app.route('/api/create-account', methods=['POST'])
def create_account_from_unity():
    try:
        data = request.json
        if data['role'] == 'guardian':
             create_guardian(mongo, data['email'], password=data['password'])
        else:
             create_patient(mongo, data['name'], data['email'], data['password'], "0000000000", data['guardian_id'])
       
        return jsonify({"status": "account created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DATA API ENDPOINTS ---

@app.route('/api/patient/info')
@login_required
def get_patient_info():
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
   
    patient = mongo.db.patients.find_one({'_id': ObjectId(current_user.id)})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
   
    return jsonify({
        "_id": str(patient['_id']),
        "name": patient.get('name', 'Patient'),
        "email": patient.get('email', ''),
        "phone": patient.get('phone', ''),
    })

@app.route('/api/patient/dashboard-data')
@login_required
def get_patient_dashboard_data():
    if current_user.role != 'patient':
        return jsonify({"error": "Unauthorized"}), 403
   
    patient_id = current_user.id
   
    # Fetch all related data
    vitals = list(mongo.db.vitals.find({'patient_id': patient_id}).sort('timestamp', -1).limit(4))
    tasks = list(mongo.db.tasks.find({'patient_id': patient_id, 'date': datetime.utcnow().strftime('%Y-%m-%d')}))
    medications = list(mongo.db.medications.find({'patient_id': patient_id}))
    appointments = list(mongo.db.appointments.find({'patient_id': patient_id, 'status': 'scheduled'}).sort('date', 1))

    # Convert ObjectIds to strings for JSON
    for item in vitals + tasks + medications + appointments:
        item['_id'] = str(item['_id'])
       
    return jsonify({
        "vitals": vitals,
        "tasks": tasks,
        "medications": medications,
        "appointments": appointments
    })

@app.route('/api/guardian/dashboard-data/<patient_id>')
@login_required
def get_guardian_patient_data(patient_id):
    if current_user.role != 'guardian':
        return jsonify({"error": "Unauthorized"}), 403

    # Fetch data for specific patient
    vitals = list(mongo.db.vitals.find({'patient_id': patient_id}).sort('timestamp', -1).limit(5))
    tasks = list(mongo.db.tasks.find({'patient_id': patient_id, 'date': datetime.utcnow().strftime('%Y-%m-%d')}))
    medications = list(mongo.db.medications.find({'patient_id': patient_id}))
    appointments = list(mongo.db.appointments.find({'patient_id': patient_id}).sort('date', 1))

    for item in vitals + tasks + medications + appointments:
        item['_id'] = str(item['_id'])

    return jsonify({
        "vitals": vitals,
        "tasks": tasks,
        "medications": medications,
        "appointments": appointments
    })

@app.route('/api/task/toggle/<task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    try:
        # Find task
        task = mongo.db.tasks.find_one({'_id': ObjectId(task_id)})
        if not task:
            return jsonify({"error": "Task not found"}), 404
           
        # Toggle status
        new_status = not task.get('is_completed', False)
        mongo.db.tasks.update_one({'_id': ObjectId(task_id)}, {'$set': {'is_completed': new_status}})
       
        return jsonify({"status": "success", "new_state": new_status})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/appointment/book', methods=['POST'])
@login_required
def book_appointment():
    try:
        data = request.json
        create_appointment(
            mongo,
            data['patient_id'],
            data['doctor_name'],
            data['specialty'],
            data['date'],
            data['time']
        )
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- UNITY AUTH ---

@app.route('/signup/unity', methods=['POST'])
def signup_unity():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        role = request.form.get('role') # 'individual' or 'ngo'
       
        # Extra fields
        age = request.form.get('age')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        purpose = request.form.get('purpose')
       
        extra_data = {
            'age': age,
            'gender': gender,
            'phone': phone,
            'purpose': purpose
        }

        if mongo.db.unity_users.find_one({'email': email}):
            return "Email already registered", 400

        result = create_unity_user(mongo, email, password, role, name, extra_data)
       
        # Auto login
        user_data = mongo.db.unity_users.find_one({'_id': result.inserted_id})
        user = User(user_data, 'unity')
        login_user(user)
       
        return redirect('/connection')

    except Exception as e:
        print(f"Error in signup_unity: {e}")
        return f"An error occurred: {str(e)}", 500

@app.route('/login/unity', methods=['POST'])
def login_unity():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
       
        user_data = mongo.db.unity_users.find_one({'email': email})
       
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data, 'unity')
            login_user(user)
            return redirect('/connection')
           
        return "Invalid credentials", 401
    except Exception as e:
        print(f"Error in login_unity: {e}")
        return f"Login failed: {str(e)}", 500

# --- PATIENT API ENDPOINTS ---

@app.route('/api/patient/info', methods=['GET'])
@login_required
def api_patient_info():
    """Returns current patient's info"""
    try:
        if current_user.role != 'patient':
            return jsonify({"error": "Unauthorized"}), 403
       
        patient = mongo.db.patients.find_one({'_id': ObjectId(current_user.id)})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
       
        return jsonify({
            "name": patient.get('name', 'Patient'),
            "email": patient.get('email'),
            "phone": patient.get('phone', 'N/A'),
            "id": str(patient.get('_id'))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/patient/dashboard-data', methods=['GET'])
@login_required
def api_patient_dashboard():
    """Returns all dashboard data for patient"""
    try:
        if current_user.role != 'patient':
            return jsonify({"error": "Unauthorized"}), 403
       
        patient_id = current_user.id
        patient = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
       
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
       
        # Fetch vitals
        vitals = list(mongo.db.vitals.find({'patient_id': patient_id}).sort('timestamp', -1).limit(10))
        for vital in vitals:
            vital['_id'] = str(vital.get('_id'))
            vital['timestamp'] = str(vital.get('timestamp'))
       
        # Fetch tasks
        from datetime import datetime as dt
        today = dt.utcnow().strftime('%Y-%m-%d')
        tasks = list(mongo.db.tasks.find({'patient_id': patient_id, 'date': today}))
        for task in tasks:
            task['_id'] = str(task.get('_id'))
       
        # Fetch medications
        medications = list(mongo.db.medications.find({'patient_id': patient_id}))
        for med in medications:
            med['_id'] = str(med.get('_id'))
       
        # Fetch appointments
        appointments = list(mongo.db.appointments.find({'patient_id': patient_id}).sort('date', -1).limit(5))
        for appt in appointments:
            appt['_id'] = str(appt.get('_id'))
       
        return jsonify({
            "vitals": vitals,
            "tasks": tasks,
            "medications": medications,
            "appointments": appointments,
            "patient_name": patient.get('name'),
            "patient_phone": patient.get('phone')
        })
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/task/toggle', methods=['POST'])
@login_required
def api_toggle_task():
    """Toggle task completion status"""
    try:
        if current_user.role != 'patient':
            return jsonify({"error": "Unauthorized"}), 403
       
        data = request.json
        task_id = data.get('task_id')
        is_completed = data.get('is_completed', False)
       
        if not task_id:
            return jsonify({"error": "Task ID required"}), 400
       
        result = mongo.db.tasks.update_one(
            {'_id': ObjectId(task_id), 'patient_id': current_user.id},
            {'$set': {'is_completed': is_completed}}
        )
       
        if result.matched_count == 0:
            return jsonify({"error": "Task not found"}), 404
       
        return jsonify({
            "status": "success",
            "message": "Task updated",
            "is_completed": is_completed
        })
    except Exception as e:
        print(f"Error toggling task: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/task/add-task', methods=['POST'])
@login_required
def api_add_task():
    """Add new task for patient"""
    try:
        if current_user.role != 'patient':
            return jsonify({"error": "Unauthorized"}), 403
       
        data = request.json
        title = data.get('title')
        description = data.get('description', '')
       
        if not title:
            return jsonify({"error": "Title required"}), 400
       
        from datetime import datetime as dt
        task = {
            'patient_id': current_user.id,
            'title': title,
            'description': description,
            'date': dt.utcnow().strftime('%Y-%m-%d'),
            'is_completed': False,
            'created_at': dt.utcnow()
        }
       
        result = mongo.db.tasks.insert_one(task)
       
        return jsonify({
            "status": "success",
            "task_id": str(result.inserted_id),
            "task": {**task, '_id': str(result.inserted_id)}
        })
    except Exception as e:
        print(f"Error adding task: {e}")
        return jsonify({"error": str(e)}), 500

# --- SOS EMERGENCY FEATURE ---

@app.route('/feature/sos/trigger', methods=['POST'])
@login_required
def sos_trigger():
    try:
        if current_user.role != 'patient':
            return jsonify({"error": "Unauthorized"}), 403
       
        patient_id = current_user.id
        patient = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
       
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
       
        guardian_id = patient.get('guardian_id')
       
        # Create SOS alert record
        sos_alert = {
            'patient_id': patient_id,
            'patient_name': patient.get('name', 'Unknown Patient'),
            'guardian_id': guardian_id,
            'timestamp': datetime.utcnow(),
            'status': 'active',
            'location': {
                'latitude': None,
                'longitude': None
            },
            'message': f"Emergency SOS alert from {patient.get('name', 'Patient')}"
        }
       
        result = mongo.db.sos_alerts.insert_one(sos_alert)
       
        # Create notification for guardian
        notification = {
            'user_id': guardian_id,
            'type': 'emergency_sos',
            'title': 'EMERGENCY SOS ALERT',
            'message': f'{patient.get("name", "Your patient")} has triggered an emergency SOS alert!',
            'patient_id': patient_id,
            'alert_id': str(result.inserted_id),
            'timestamp': datetime.utcnow(),
            'read': False,
            'priority': 'critical'
        }
       
        mongo.db.notifications.insert_one(notification)
       
        print(f"🚨 SOS ALERT TRIGGERED: Patient {patient.get('name')} (ID: {patient_id})")
       
        return jsonify({
            "status": "success",
            "message": "Emergency alert sent to your guardian",
            "alert_id": str(result.inserted_id)
        })
       
    except Exception as e:
        print(f"Error in SOS trigger: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/feature/sos/dashboard')
@login_required
def sos_dashboard():
    try:
        if current_user.role != 'patient':
            return redirect('/patient-dashboard')
       
        patient_id = current_user.id
       
        # Fetch active SOS alerts
        sos_alerts = list(mongo.db.sos_alerts.find({'patient_id': patient_id}).sort('timestamp', -1))
       
        for alert in sos_alerts:
            alert['_id'] = str(alert['_id'])
            alert['timestamp'] = str(alert['timestamp'])
       
        return jsonify({
            "alerts": sos_alerts,
            "active_count": sum(1 for alert in sos_alerts if alert['status'] == 'active')
        })
       
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
# ═══════════════════════════════════════════════════════════
# 🎙️ COMPREHENSIVE VOICE ASSISTANT — Flask Routes
# ═══════════════════════════════════════════════════════════
import json as _json
# Gemini imported conditionally below

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_gemini_model = None
try:
    import google.generativeai as _genai
    if GEMINI_API_KEY:
        _genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = _genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=_genai.types.GenerationConfig(temperature=0.35, max_output_tokens=400)
        )
except Exception as _ge:
    print(f"[Gemini] Not available: {_ge}")


@app.route('/voice-assistant')
@login_required
def voice_assistant_page():
    return render_template('voice-assistant.html', role=current_user.role)


@app.route('/api/voice/context', methods=['GET'])
@login_required
def voice_context():
    """Return live user context so the assistant can answer data questions."""
    try:
        ctx = { "role": current_user.role, "name": "User" }
        pid = current_user.id

        if current_user.role == 'patient':
            pat = mongo.db.patients.find_one({'_id': ObjectId(pid)})
            if pat:
                ctx["name"] = pat.get("name", "Patient")
                ctx["phone"] = pat.get("phone", "")

            today = datetime.utcnow().strftime('%Y-%m-%d')
            vitals = list(mongo.db.vitals.find({'patient_id': pid}).sort('timestamp',-1).limit(5))
            tasks  = list(mongo.db.tasks.find({'patient_id': pid, 'date': today}))
            meds   = list(mongo.db.medications.find({'patient_id': pid}))
            appts  = list(mongo.db.appointments.find({'patient_id': pid, 'status':'scheduled'}).sort('date',1).limit(3))
            notifs = list(mongo.db.notifications.find({'user_id': pid, 'is_read': False}).limit(5))

            for lst in [vitals, tasks, meds, appts, notifs]:
                for x in lst: x['_id'] = str(x.get('_id',''))

            ctx.update({
                "vitals":        [{"type": v.get("type"), "value": v.get("value"), "unit": v.get("unit")} for v in vitals],
                "tasks":         [{"title": t.get("title"), "done": t.get("is_completed", False)} for t in tasks],
                "medications":   [{"name": m.get("name"), "dosage": m.get("dosage"), "time": m.get("time_of_day")} for m in meds],
                "appointments":  [{"doctor": a.get("doctor_name"), "date": a.get("date"), "time": a.get("time")} for a in appts],
                "unread_notifs": len(notifs),
            })

        elif current_user.role == 'guardian':
            guard = mongo.db.guardians.find_one({'_id': ObjectId(pid)})
            patients = list(mongo.db.patients.find({'guardian_id': pid}))
            for p in patients: p['_id'] = str(p.get('_id',''))
            ctx["name"] = guard.get("email", "Guardian") if guard else "Guardian"
            ctx["patients"] = [{"name": p.get("name"), "id": p.get("_id"), "emergency": p.get("is_emergency", False)} for p in patients]

        return jsonify(ctx)
    except Exception as e:
        return jsonify({"role": current_user.role, "name": "User", "error": str(e)})


@app.route('/api/voice/chat', methods=['POST'])
@login_required
def voice_chat():
    """Main Gemini conversation endpoint."""
    data      = request.json or {}
    user_text = data.get('text', '').strip()
    lang_name = data.get('lang_name', 'English')
    ctx       = data.get('context', {})
    history   = data.get('history', [])   # last N turns for multi-turn
    role      = current_user.role

    if not user_text:
        return jsonify({"error": "Empty input"}), 400

    # ── Build rich role context ──
    if role == 'patient':
        vitals_str = ", ".join([f"{v['type']}: {v['value']} {v['unit']}" for v in ctx.get('vitals', [])]) or "no vitals recorded"
        tasks_str  = ", ".join([f"{'✅' if t['done'] else '⬜'} {t['title']}" for t in ctx.get('tasks', [])]) or "no tasks today"
        meds_str   = ", ".join([f"{m['name']} {m['dosage']} ({m['time']})" for m in ctx.get('medications', [])]) or "no medications"
        appt_str   = ", ".join([f"Dr. {a['doctor']} on {a['date']} at {a['time']}" for a in ctx.get('appointments', [])]) or "no upcoming appointments"
        role_ctx = f"""
USER: Patient named {ctx.get('name','Patient')} | Phone: {ctx.get('phone','')}
TODAY'S VITALS: {vitals_str}
TODAY'S TASKS: {tasks_str}
MEDICATIONS: {meds_str}
UPCOMING APPOINTMENTS: {appt_str}
UNREAD NOTIFICATIONS: {ctx.get('unread_notifs', 0)}

AVAILABLE SECTIONS IN APP:
- "My Day" / home dashboard (tab: p-home) — daily tasks, vitals, schedule, care team
- "Medicine" / Digital Pharmacy (tab: p-medicine) — medication list, refills, intake timeline
- "My Profile" (tab: p-profile) — personal info, medical ID, records
- "Connections" (/connection) — volunteers, Unity Hub
- "Notifications" (/notifications) — alerts from care team
- "SOS Emergency" — triggers guardian alert immediately

ACTIONS PATIENT CAN TRIGGER:
- Navigate to any section/tab
- Mark a task complete (COMPLETE_TASK)
- Request medication refill (REQUEST_REFILL)
- Trigger SOS (TRIGGER_SOS)
- Logout (LOGOUT)
"""
    elif role == 'guardian':
        pts = ctx.get('patients', [])
        pts_str = ", ".join([f"{p['name']}" + (" ⚠️EMERGENCY" if p.get('emergency') else "") for p in pts]) or "no patients"
        role_ctx = f"""
USER: Guardian | Patients: {pts_str}

AVAILABLE SECTIONS IN GUARDIAN DASHBOARD:
- "Home" (tab: home-view) — overview, sessions, quick nav cards
- "Daily Updates" (tab: daily-updates-view) — vitals, adherence, medication tracking
- "Consultations" (tab: consultation-view) — book appointments, calendar
- "Patient Profile" (tab: patient-profile) — medical records, upload documents
- "Preferences" (tab: preferences-view) — notifications, diet, lifestyle
- "Unity Hub" (/connection) — volunteers and community
- Settings (openSettings modal)

ACTIONS GUARDIAN CAN TRIGGER:
- Navigate to any section/tab
- Book an appointment (BOOK_APPOINTMENT)
- Open settings (OPEN_SETTINGS)
- Print medical report (PRINT_REPORT)
- Trigger SOS for patient (TRIGGER_SOS)
- Logout (LOGOUT)
"""
    else:
        role_ctx = "USER: Unity Hub member. Available: Connections (/connection), Logout."

    # Build conversation history string
    hist_str = ""
    for turn in history[-4:]:
        hist_str += f"User: {turn.get('user','')}\nAssistant: {turn.get('bot','')}\n"

    prompt = f"""
You are GoldenSage Voice Assistant — a warm, intelligent, multilingual AI embedded inside the GoldenSage senior health app in India.

{role_ctx}

INSTRUCTIONS:
1. Reply ONLY in {lang_name}. Use warm, respectful, simple language for elderly users.
2. You have full awareness of the user's live health data above — use it to give personalised answers.
3. Identify the user's intent and return ONE of these actions (or null):
   NAVIGATE_HOME, NAVIGATE_MEDICINE, NAVIGATE_PROFILE, NAVIGATE_CONNECTIONS,
   NAVIGATE_NOTIFICATIONS, NAVIGATE_DAILY_UPDATES, NAVIGATE_CONSULTATIONS,
   NAVIGATE_PATIENT_PROFILE, NAVIGATE_PREFERENCES,
   TRIGGER_SOS, COMPLETE_TASK, REQUEST_REFILL, BOOK_APPOINTMENT,
   OPEN_SETTINGS, PRINT_REPORT, LOGOUT
4. Keep reply SHORT (2–3 sentences max). It will be spoken aloud to an elderly person.
5. If user asks about their vitals/tasks/meds, answer from the live data provided.
6. If user seems confused, gently explain what sections are available.
7. Never give medical diagnoses. Say "please consult your doctor."
8. For SOS or Logout, confirm intent before acting.
9. Use respectful address ("आप", "আপনি", "நீங்கள்" etc.) in non-English languages.

Previous conversation:
{hist_str}

Respond with valid JSON only (absolutely no markdown fences or extra text):
{{
  "reply": "<spoken reply in {lang_name}>",
  "action": "<action string or null>",
  "action_data": {{<any extra data needed, e.g. task_title for COMPLETE_TASK>}},
  "confidence": <0.0-1.0>
}}

User said: "{user_text}"
"""

    try:
        if _gemini_model:
            resp = _gemini_model.generate_content(prompt)
            raw  = resp.text.strip().replace("```json","").replace("```","").strip()
            result = _json.loads(raw)
        else:
            result = _voice_fallback(user_text, role)

        action = result.get('action')
        nav    = _action_to_nav(action, role)

        return jsonify({
            "reply":       result.get('reply', 'I am here to help.'),
            "action":      action,
            "action_data": result.get('action_data', {}),
            "url":         nav.get('url'),
            "tab":         nav.get('tab'),
            "js_call":     nav.get('js_call'),
        })

    except Exception as e:
        print(f"[VoiceChat Error] {e}")
        return jsonify({"reply": "I had a small problem. Please try again.", "action": None, "url": None, "tab": None, "js_call": None})


def _action_to_nav(action, role):
    """Map action string → { url, tab, js_call }."""
    # Patient nav
    if action == 'NAVIGATE_HOME':           return {'url': '/patient-dashboard',  'tab': 'p-home',      'js_call': None}
    if action == 'NAVIGATE_MEDICINE':       return {'url': '/patient-dashboard',  'tab': 'p-medicine',  'js_call': None}
    if action == 'NAVIGATE_PROFILE':        return {'url': '/patient-dashboard',  'tab': 'p-profile',   'js_call': None}
    if action == 'NAVIGATE_CONNECTIONS':    return {'url': '/connection',          'tab': None,          'js_call': None}
    if action == 'NAVIGATE_NOTIFICATIONS':  return {'url': '/notifications',       'tab': None,          'js_call': None}
    # Guardian nav
    if action == 'NAVIGATE_DAILY_UPDATES':  return {'url': '/guardian-dashboard', 'tab': 'daily-updates-view',  'js_call': None}
    if action == 'NAVIGATE_CONSULTATIONS':  return {'url': '/guardian-dashboard', 'tab': 'consultation-view',   'js_call': None}
    if action == 'NAVIGATE_PATIENT_PROFILE':return {'url': '/guardian-dashboard', 'tab': 'patient-profile',     'js_call': None}
    if action == 'NAVIGATE_PREFERENCES':    return {'url': '/guardian-dashboard', 'tab': 'preferences-view',    'js_call': None}
    if action == 'OPEN_SETTINGS':           return {'url': None,                  'tab': None,          'js_call': 'openSettings()'}
    if action == 'PRINT_REPORT':            return {'url': None,                  'tab': None,          'js_call': 'printMedicalReport()'}
    if action == 'BOOK_APPOINTMENT':        return {'url': '/guardian-dashboard', 'tab': 'consultation-view',   'js_call': 'openCalendar()'}
    # Shared
    if action == 'TRIGGER_SOS':             return {'url': '/feature/sos/trigger','tab': None,          'js_call': None}
    if action == 'LOGOUT':                  return {'url': '/signout',            'tab': None,          'js_call': None}
    return {}


def _voice_fallback(text, role):
    t = text.lower()
    if any(w in t for w in ['home','dashboard','my day','ghar','aaj','today','शुरू','আজ']):
        return {"reply":"Taking you home.","action":"NAVIGATE_HOME","action_data":{},"confidence":0.9}
    if any(w in t for w in ['medicine','medic','pharmacy','dawa','dawai','tablet','pill','दवा','ওষুধ']):
        return {"reply":"Opening medicines.","action":"NAVIGATE_MEDICINE","action_data":{},"confidence":0.9}
    if any(w in t for w in ['profile','account','personal','मेरा','আমার']):
        return {"reply":"Opening your profile.","action":"NAVIGATE_PROFILE","action_data":{},"confidence":0.9}
    if any(w in t for w in ['notif','alert','remind','सूचना','বিজ্ঞপ্তি']):
        return {"reply":"Opening notifications.","action":"NAVIGATE_NOTIFICATIONS","action_data":{},"confidence":0.9}
    if any(w in t for w in ['connect','volunteer','unity','community']):
        return {"reply":"Going to connections.","action":"NAVIGATE_CONNECTIONS","action_data":{},"confidence":0.9}
    if any(w in t for w in ['vital','update','daily','chart']):
        return {"reply":"Opening daily updates.","action":"NAVIGATE_DAILY_UPDATES","action_data":{},"confidence":0.9}
    if any(w in t for w in ['consult','appointment','book','doctor','calendar']):
        return {"reply":"Opening consultations.","action":"NAVIGATE_CONSULTATIONS","action_data":{},"confidence":0.9}
    if any(w in t for w in ['setting','prefer','dark','font']):
        return {"reply":"Opening settings.","action":"OPEN_SETTINGS","action_data":{},"confidence":0.9}
    if any(w in t for w in ['print','report','export','record']):
        return {"reply":"Printing medical report.","action":"PRINT_REPORT","action_data":{},"confidence":0.9}
    if any(w in t for w in ['sos','emergency','help','danger','bachao','बचाओ','সাহায্য']):
        return {"reply":"Sending SOS emergency alert!","action":"TRIGGER_SOS","action_data":{},"confidence":0.95}
    if any(w in t for w in ['logout','sign out','log out','bahar','बाहर']):
        return {"reply":"Logging you out.","action":"LOGOUT","action_data":{},"confidence":0.9}
    return {"reply":"I'm here to help! Try: go home, medicines, my profile, book appointment, or SOS.","action":None,"action_data":{},"confidence":0.2}

# ═══════════════════════════════════════════════════════════════
# 🎙️ VOICE ASSISTANT — comprehensive routes
# ═══════════════════════════════════════════════════════════════

@app.route('/voice-assistant')
@login_required
def voice_assistant():
    return render_template(
        'voice-assistant.html',
        role=current_user.role,
        name=getattr(current_user, 'name', current_user.email)
    )


@app.route('/api/voice/chat', methods=['POST'])
@login_required
def voice_chat():
    import json as _json

    data      = request.json or {}
    user_text = data.get('text', '').strip()
    lang_name = data.get('lang_name', 'English')
    role      = current_user.role  # patient | guardian | unity

    if not user_text:
        return jsonify({'error': 'No input'}), 400

    # ── Role-specific navigation actions ──
    ACTIONS_BY_ROLE = {
        'patient': """
NAVIGATE_HOME           → My Day / Home dashboard tab (p-home)
NAVIGATE_MEDICINE       → Digital Pharmacy / Medicine tab (p-medicine)
NAVIGATE_PROFILE        → My Profile tab (p-profile)
NAVIGATE_CONNECTIONS    → /connection page (Unity Hub / volunteers)
NAVIGATE_NOTIFICATIONS  → /notifications page
TRIGGER_SOS             → Send emergency SOS alert to guardian immediately
LOGOUT                  → Sign the user out
""",
        'guardian': """
NAVIGATE_GUARDIAN_HOME   → Guardian home tab (home-view)
NAVIGATE_DAILY_UPDATES   → Daily Updates / vitals tab (daily-updates-view)
NAVIGATE_CONSULTATIONS   → Consultations / book appointment tab (consultation-view)
NAVIGATE_PATIENT_PROFILE → Patient Profile / Identity & Health tab (patient-profile)
NAVIGATE_PREFERENCES     → Preferences tab (preferences-view)
NAVIGATE_CONNECTIONS     → /connection page (Unity Hub)
NAVIGATE_NOTIFICATIONS   → /notifications page
PRINT_REPORT             → Print patient medical report (triggers browser print)
OPEN_SETTINGS            → Open the Settings modal
LOGOUT                   → Sign the user out
""",
        'unity': """
NAVIGATE_CONNECTIONS    → /connection page (Unity Hub feed)
NAVIGATE_NOTIFICATIONS  → /notifications page
LOGOUT                  → Sign the user out
"""
    }

    # ── Knowledge base for FAQ answers ──
    KNOWLEDGE = {
        'patient': """
APP SECTIONS:
- My Day (home): Daily tasks with check buttons, vitals (heart rate/BP/blood sugar), upcoming appointments, care team doctors.
- Medicine (Digital Pharmacy): Medicine list with dosage/timing, intake timeline (morning/noon/night), refill buttons, stock levels.
- My Profile: Personal info (name, phone, DOB), medical history, allergy warnings, active medication list, medical ID card.
- Connections (Unity Hub): Volunteer community, NGO posts, mentors, peer support feed.
- Notifications: Alerts from guardian/care team, medication reminders, SOS acknowledgements.

ACTIONS AVAILABLE:
- Mark tasks complete: tap the green check button on My Day.
- Request medicine refill: click "Refill Now" on any medicine card in the Medicine section.
- Trigger SOS emergency: say "SOS" or "I need help" — alert goes to guardian immediately.
- View vitals: shown automatically on My Day dashboard.
- Check appointments: visible in the My Day home section.
""",
        'guardian': """
APP SECTIONS:
- Home: Overview with upcoming sessions, session history, quick navigation cards.
- Daily Updates: Live patient vitals (heart rate, BP, blood sugar), daily lifestyle adherence, medication compliance, routine tasks.
- Consultations: Book new doctor appointments — pick doctor, select date on calendar, choose time slot.
- Patient Profile: Full medical identity — DOB, blood type, allergies, medication list, medical history, emergency contact.
- Preferences: Settings for notifications, dark mode, text size, guardian preferences.
- Unity Hub / Connections: Volunteer and NGO community connections page.
- Notifications: All alerts including SOS alarms, medication missed alerts, task completion updates.
- Settings modal: Dark mode toggle, large text mode, notification preferences.

ACTIONS AVAILABLE:
- Book consultation: go to Consultations tab, select doctor, pick date, choose time slot.
- Check vitals: Daily Updates tab shows real-time patient vitals.
- Print medical report: triggers a formatted print window with patient details, allergies, medications, emergency contact.
- Check SOS: SOS alerts appear in Notifications — also auto-checked every 10 seconds by the dashboard.
""",
        'unity': """
APP SECTIONS:
- Unity Hub Feed: Social feed with posts from students, NGOs, mentors, elderly patients.
- Tabs: All Feed, Students & Elderly, NGO Aid, Patient Circle.
- Stories: Upload short videos as stories.
- Messages: Direct messaging via paper-plane icon.
- Notifications: Likes and activity notifications via heart icon.
"""
    }

    prompt = f"""
You are GoldenSage Voice Assistant — embedded inside the GoldenSage senior health web app in India.
You are speaking directly to a {role.upper()} user.
You must respond ONLY in {lang_name}. Be warm, gentle, patient — this is likely an elderly user or their caregiver.
Keep your reply SHORT (max 2–3 sentences) — it will be spoken aloud by the app.

=== APP KNOWLEDGE ===
{KNOWLEDGE.get(role, KNOWLEDGE['patient'])}

=== NAVIGATION ACTIONS YOU CAN TRIGGER ===
{ACTIONS_BY_ROLE.get(role, ACTIONS_BY_ROLE['patient'])}

=== RULES ===
1. Respond ONLY in {lang_name}. Use warm, simple language.
2. If the user wants to navigate somewhere, set the action field.
3. If they ask a question about the app, answer it using the knowledge base above.
4. If they seem distressed or ask for help urgently, suggest TRIGGER_SOS.
5. Never give medical advice. Say "please consult your doctor" for medical questions.
6. Keep reply to 1–3 short sentences (spoken aloud).
7. For SOS and Logout — always confirm verbally in the reply.

=== RESPONSE FORMAT ===
Respond with VALID JSON ONLY. No markdown. No code fences.
{{
  "reply": "<warm reply in {lang_name}, max 3 sentences>",
  "action": "<action name from the list above, or null if just answering a question>",
  "confidence": <0.0-1.0>
}}

User ({role}) said: "{user_text}"
"""

    try:
        if _gmodel:
            raw = _gmodel.generate_content(prompt).text.strip()
            raw = raw.replace('```json','').replace('```','').strip()
            result = _json.loads(raw)
        else:
            result = _voice_fallback(user_text, role)

        action = result.get('action') or 'null'

        # Map action → url + tab
        ACTION_ROUTES = {
            'NAVIGATE_HOME':           ('/patient-dashboard',  'p-home'),
            'NAVIGATE_MEDICINE':       ('/patient-dashboard',  'p-medicine'),
            'NAVIGATE_PROFILE':        ('/patient-dashboard',  'p-profile'),
            'NAVIGATE_GUARDIAN_HOME':  ('/guardian-dashboard', 'home-view'),
            'NAVIGATE_DAILY_UPDATES':  ('/guardian-dashboard', 'daily-updates-view'),
            'NAVIGATE_CONSULTATIONS':  ('/guardian-dashboard', 'consultation-view'),
            'NAVIGATE_PATIENT_PROFILE':('/guardian-dashboard', 'patient-profile'),
            'NAVIGATE_PREFERENCES':    ('/guardian-dashboard', 'preferences-view'),
            'NAVIGATE_CONNECTIONS':    ('/connection',          None),
            'NAVIGATE_NOTIFICATIONS':  ('/notifications',       None),
            'NAVIGATE_MAIN':           ('/main',                None),
            'TRIGGER_SOS':             ('/feature/sos/trigger', None),
            'PRINT_REPORT':            (None,                   None),
            'OPEN_SETTINGS':           (None,                   None),
            'LOGOUT':                  ('/signout',             None),
        }
        url, tab = ACTION_ROUTES.get(action, (None, None))

        return jsonify({
            'reply':  result.get('reply', 'I am here to help you.'),
            'action': action,
            'url':    url,
            'tab':    tab,
        })

    except Exception as e:
        print(f'[VoiceChat Error] {e}')
        return jsonify({'reply': 'I had a small problem. Please try again.', 'action': None, 'url': None, 'tab': None})


def _voice_fallback(text, role):
    """Keyword fallback when no Gemini API key is configured."""
    t = text.lower()
    # SOS — highest priority
    if any(w in t for w in ['sos','emergency','help','danger','bachao','madad','alarm']):
        return {'reply':'Sending SOS to your guardian now!','action':'TRIGGER_SOS','confidence':.95}
    # Logout
    if any(w in t for w in ['logout','log out','sign out','bahar','niklo']):
        return {'reply':'Logging you out.','action':'LOGOUT','confidence':.9}
    # Notifications
    if any(w in t for w in ['notif','alert','reminder','suchna','suchnaye']):
        return {'reply':'Opening Notifications.','action':'NAVIGATE_NOTIFICATIONS','confidence':.9}
    # Connections
    if any(w in t for w in ['connect','volunteer','unity','ngo','community','jodo']):
        return {'reply':'Going to Connections.','action':'NAVIGATE_CONNECTIONS','confidence':.9}
    # Guardian-specific
    if role == 'guardian':
        if any(w in t for w in ['print','report','medical']):
            return {'reply':'Printing the medical report now.','action':'PRINT_REPORT','confidence':.9}
        if any(w in t for w in ['setting','dark','mode','preference']):
            return {'reply':'Opening settings.','action':'OPEN_SETTINGS','confidence':.9}
        if any(w in t for w in ['vital','update','daily','blood','heart','pressure','sugar']):
            return {'reply':'Opening Daily Updates.','action':'NAVIGATE_DAILY_UPDATES','confidence':.9}
        if any(w in t for w in ['consult','appointment','book','doctor','schedule']):
            return {'reply':'Opening Consultations.','action':'NAVIGATE_CONSULTATIONS','confidence':.9}
        if any(w in t for w in ['patient profile','identity','record','allergy']):
            return {'reply':'Opening Patient Profile.','action':'NAVIGATE_PATIENT_PROFILE','confidence':.9}
        if any(w in t for w in ['preference','prefer']):
            return {'reply':'Opening Preferences.','action':'NAVIGATE_PREFERENCES','confidence':.9}
        return {'reply':'Taking you to the Guardian Dashboard.','action':'NAVIGATE_GUARDIAN_HOME','confidence':.7}
    # Patient-specific
    if any(w in t for w in ['medicine','medic','dawa','dawai','pill','tablet','pharmacy','dava','refill']):
        return {'reply':'Opening your medicines.','action':'NAVIGATE_MEDICINE','confidence':.9}
    if any(w in t for w in ['profile','account','personal','mera','details']):
        return {'reply':'Opening your profile.','action':'NAVIGATE_PROFILE','confidence':.9}
    if any(w in t for w in ['home','dashboard','ghar','my day','aaj','today','main']):
        return {'reply':'Taking you home.','action':'NAVIGATE_HOME','confidence':.9}
    return {'reply':'I\'m here! Try: go home, medicines, my profile, notifications, or SOS.','action':None,'confidence':.2}