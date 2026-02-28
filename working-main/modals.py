from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime

class User(UserMixin):
    def __init__(self, user_data, role):
        self.id = str(user_data.get('_id'))
        self.name = user_data.get('name')
        self.email = user_data.get('email')
        self.role = role
        self.password_hash = user_data.get('password')
        self.guardian_id = user_data.get('guardian_id')
        
    def get_id(self):
        # We prefix the ID with role to distinguish between collections
        return f"{self.role}:{self.id}"

    @staticmethod
    def get_user_by_id(mongo, user_id):
        # Split prefix: "guardian:123abc..." -> ["guardian", "123abc..."]
        try:
            role, db_id = user_id.split(':', 1)
            if role == 'guardian':
                collection = mongo.db.guardians
            elif role == 'patient':
                collection = mongo.db.patients
            elif role == 'unity':
                collection = mongo.db.unity_users
            else:
                return None
                
            data = collection.find_one({'_id': ObjectId(db_id)})
            if data:
                return User(data, role)
        except:
            return None
        return None

# Helper functions for database operations
def create_guardian(mongo, email, password):
    return mongo.db.guardians.insert_one({
        'email': email,
        'password': generate_password_hash(password),
        'created_at': datetime.utcnow()
    })

def create_patient(mongo, name, email, password, phone, guardian_id):
    return mongo.db.patients.insert_one({
        'name': name,
        'email': email,
        'password': generate_password_hash(password),
        'phone': phone,
        'guardian_id': guardian_id, # Store as string or ObjectId depending on preference
        'medical_records': None,
        'is_emergency': False,
        'created_at': datetime.utcnow()
    })

def create_notification(mongo, user_id, message):
    return mongo.db.notifications.insert_one({
        'user_id': user_id, # Link to guardian_id
        'message': message,
        'timestamp': datetime.utcnow(),
        'is_read': False
    })

def create_unity_user(mongo, email, password, role, name, extra_data=None):
    return mongo.db.unity_users.insert_one({
        'email': email,
        'password': generate_password_hash(password),
        'role': role,
        'name': name,
        'extra_data': extra_data or {},
        'created_at': datetime.utcnow()
    })

# --- NEW MODELS ---

def create_vital(mongo, patient_id, vital_type, value, unit):
    return mongo.db.vitals.insert_one({
        'patient_id': patient_id, # ObjectId or string
        'type': vital_type, # e.g., 'Heart Rate', 'Blood Pressure'
        'value': value,
        'unit': unit,
        'timestamp': datetime.utcnow()
    })

def create_medication(mongo, patient_id, name, dosage, time_of_day, stock):
    return mongo.db.medications.insert_one({
        'patient_id': patient_id,
        'name': name,
        'dosage': dosage,
        'time_of_day': time_of_day, # e.g., 'Morning', 'Afternoon'
        'stock': int(stock),
        'created_at': datetime.utcnow()
    })

def create_appointment(mongo, patient_id, doctor_name, specialty, date_str, time_str):
    return mongo.db.appointments.insert_one({
        'patient_id': patient_id,
        'doctor_name': doctor_name,
        'specialty': specialty,
        'date': date_str, # Keep as string for simplicity in demo or parse to datetime
        'time': time_str,
        'status': 'scheduled',
        'created_at': datetime.utcnow()
    })

def create_task(mongo, patient_id, title, description):
    return mongo.db.tasks.insert_one({
        'patient_id': patient_id,
        'title': title,
        'description': description,
        'is_completed': False,
        'date': datetime.utcnow().strftime('%Y-%m-%d'), # Daily task for today
        'created_at': datetime.utcnow()
    })