import pymongo
from werkzeug.security import generate_password_hash
from datetime import datetime
from bson.objectid import ObjectId

# Setup connection
MONGO_URI = "mongodb://localhost:27017/seniorcare"
client = pymongo.MongoClient(MONGO_URI)
db = client.get_database() # Defaults to 'seniorcare' from URI

def seed_database():
    print("🌱 Seeding Database...")

    # 1. Create Dummy Guardian
    guardian_email = "demo@guardian.com"
    guardian_password = "password123"
    
    existing_guardian = db.guardians.find_one({'email': guardian_email})
    if existing_guardian:
        print(f"Guardian {guardian_email} already exists. Skipping creation.")
        guardian_id = existing_guardian['_id']
    else:
        print(f"Creating Guardian: {guardian_email}")
        result = db.guardians.insert_one({
            'email': guardian_email,
            'password': generate_password_hash(guardian_password),
            'created_at': datetime.utcnow()
        })
        guardian_id = result.inserted_id

    # 2. Create Dummy Patient
    patient_email = "grandpa@patient.com"
    
    existing_patient = db.patients.find_one({'email': patient_email})
    if existing_patient:
        print(f"Patient {patient_email} already exists. Skipping creation.")
        patient_id = existing_patient['_id']
    else:
        print(f"Creating Patient: {patient_email}")
        result = db.patients.insert_one({
            'name': "Grandpa",
            'email': patient_email,
            'password': generate_password_hash("password123"),
            'phone': "555-0199",
            'guardian_id': guardian_id,
            'medical_records': None,
            'is_emergency': False,
            'created_at': datetime.utcnow()
        })
        patient_id = result.inserted_id

    # 3. Add Demo Vitals
    print("Adding demo vitals...")
    vitals_data = [
        {'patient_id': str(patient_id), 'type': 'Heart Rate', 'value': 72, 'unit': 'bpm', 'timestamp': datetime.utcnow()},
        {'patient_id': str(patient_id), 'type': 'Blood Pressure', 'value': '120/80', 'unit': 'mmHg', 'timestamp': datetime.utcnow()},
        {'patient_id': str(patient_id), 'type': 'Blood Sugar', 'value': 110, 'unit': 'mg/dL', 'timestamp': datetime.utcnow()},
    ]
    db.vitals.insert_many(vitals_data)

    # 4. Add Demo Tasks
    print("Adding demo tasks...")
    tasks_data = [
        {'patient_id': str(patient_id), 'title': 'Morning Medication', 'description': 'Lisinopril • 10mg after breakfast', 'date': datetime.utcnow().strftime('%Y-%m-%d'), 'is_completed': True},
        {'patient_id': str(patient_id), 'title': 'Physiotherapy Walk', 'description': '15 mins light walking in the garden', 'date': datetime.utcnow().strftime('%Y-%m-%d'), 'is_completed': False},
        {'patient_id': str(patient_id), 'title': 'Blood Pressure Check', 'description': 'Log reading before lunch', 'date': datetime.utcnow().strftime('%Y-%m-%d'), 'is_completed': False},
        {'patient_id': str(patient_id), 'title': 'Afternoon Vitamin', 'description': 'Vitamin D3 • During lunch', 'date': datetime.utcnow().strftime('%Y-%m-%d'), 'is_completed': False},
    ]
    db.tasks.insert_many(tasks_data)

    # 5. Add Demo Medications
    print("Adding demo medications...")
    medications_data = [
        {'patient_id': str(patient_id), 'name': 'Lisinopril', 'dosage': '10mg', 'time_of_day': 'Morning', 'frequency': 'Daily'},
        {'patient_id': str(patient_id), 'name': 'Metformin', 'dosage': '500mg', 'time_of_day': 'Twice Daily', 'frequency': 'Daily'},
        {'patient_id': str(patient_id), 'name': 'Atorvastatin', 'dosage': '20mg', 'time_of_day': 'Nightly', 'frequency': 'Daily'},
        {'patient_id': str(patient_id), 'name': 'Vitamin D3', 'dosage': '2000 IU', 'time_of_day': 'Daily', 'frequency': 'Daily'},
    ]
    db.medications.insert_many(medications_data)

    # 6. Add Demo Appointments
    print("Adding demo appointments...")
    appointments_data = [
        {'patient_id': str(patient_id), 'doctor_name': 'Dr. Sarah Chen', 'doctor_specialty': 'Cardiologist', 'date': '2026-03-05', 'time': '10:00 AM', 'status': 'scheduled'},
        {'patient_id': str(patient_id), 'doctor_name': 'Dr. Elizabeth Sterling', 'doctor_specialty': 'Physiotherapist', 'date': '2026-03-02', 'time': '02:00 PM', 'status': 'scheduled'},
    ]
    db.appointments.insert_many(appointments_data)

    # 3. Create Dummy Unity User (Student)
    unity_email = "student@unity.com"
    existing_unity = db.unity_users.find_one({'email': unity_email})
    if not existing_unity:
        print(f"Creating Unity User: {unity_email}")
        db.unity_users.insert_one({
            'email': unity_email,
            'password': generate_password_hash("password123"),
            'role': "individual",
            'name': "Alex Student",
            'extra_data': {
                'age': 22,
                'gender': 'Male',
                'phone': '555-0000',
                'purpose': 'Volunteering'
            },
            'created_at': datetime.utcnow()
        })

    # 4. Add Dummy Notifications
    print("Adding sample notifications...")
    db.notifications.insert_one({
        'user_id': guardian_id,
        'message': "💊 Grandpa missed his afternoon medication.",
        'timestamp': datetime.utcnow(),
        'is_read': False
    })
    db.notifications.insert_one({
        'user_id': guardian_id,
        'message': "✅ Grandpa completed his morning walk.",
        'timestamp': datetime.utcnow(),
        'is_read': False
    })
    
    print("\n✅ Database Seeded Successfully!")
    print("=" * 50)
    print("   DEMO CREDENTIALS & DATA")
    print("=" * 50)
    print("\n🔐 GUARDIAN LOGIN")
    print(f"   Email:       demo@guardian.com")
    print(f"   Password:    password123")
    print(f"   Portal:      /login/guardian or /guardian-dashboard")
    print(f"   Patient:     Grandpa (72 years old)")
    print("\n🏥 PATIENT LOGIN")
    print(f"   Email:       grandpa@patient.com")
    print(f"   Password:    password123")
    print(f"   Portal:      /login/patient or /patient-dashboard")
    print(f"   Name:        Grandpa")
    print(f"   Phone:       555-0199")
    print("\n📊 DEMO DATA SEEDED:")
    print(f"   ✓ Vitals (3): Heart Rate, BP, Blood Sugar")
    print(f"   ✓ Tasks (4): Morning Meds, Walk, BP Check, Vitamin")
    print(f"   ✓ Medications (4): Lisinopril, Metformin, Atorvastatin, Vitamin D3")
    print(f"   ✓ Appointments (2): Cardiology, Physiotherapy")
    print(f"   ✓ Notifications (2): Medication & Activity alerts")
    print("\n🎓 UNITY HUB LOGIN (Student/NGO)")
    print(f"   Email:       student@unity.com")
    print(f"   Password:    password123")
    print(f"   Portal:      /unityhub/auth")
    print("=" * 50)

if __name__ == "__main__":
    seed_database()
