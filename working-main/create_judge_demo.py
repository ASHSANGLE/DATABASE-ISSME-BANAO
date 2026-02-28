#!/usr/bin/env python3
"""
Script to create demo accounts for judges to test the GoldenSage application
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/seniorcare')
client = MongoClient(MONGO_URI)
db = client.get_database('seniorcare')

def create_demo_accounts():
    """Create demo accounts for judges"""
    
    print("=" * 60)
    print("Creating Demo Accounts for Judges - GoldenSage")
    print("=" * 60)
    
    # Demo Guardian Account
    guardian_email = "judge@goldensage.demo"
    guardian_password = "Demo123!@#"
    
    print(f"\n📋 GUARDIAN ACCOUNT")
    print(f"Email: {guardian_email}")
    print(f"Password: {guardian_password}")
    
    # Check if guardian already exists
    existing_guardian = db.guardians.find_one({'email': guardian_email})
    if existing_guardian:
        print(f"✓ Guardian already exists with ID: {existing_guardian['_id']}")
        guardian_id = existing_guardian['_id']
    else:
        guardian_result = db.guardians.insert_one({
            'email': guardian_email,
            'password': generate_password_hash(guardian_password),
            'created_at': datetime.utcnow()
        })
        guardian_id = guardian_result.inserted_id
        print(f"✓ Guardian created with ID: {guardian_id}")
    
    # Demo Patient Account
    patient_name = "Mr. Rajesh Kumar"
    patient_email = "rajesh@goldensage.demo"
    patient_password = "Patient123!@#"
    patient_phone = "9876543210"
    
    print(f"\n👤 PATIENT ACCOUNT")
    print(f"Name: {patient_name}")
    print(f"Email: {patient_email}")
    print(f"Password: {patient_password}")
    print(f"Phone: {patient_phone}")
    
    # Check if patient already exists
    existing_patient = db.patients.find_one({'email': patient_email})
    if existing_patient:
        print(f"✓ Patient already exists with ID: {existing_patient['_id']}")
        patient_id = existing_patient['_id']
    else:
        patient_result = db.patients.insert_one({
            'name': patient_name,
            'email': patient_email,
            'password': generate_password_hash(patient_password),
            'phone': patient_phone,
            'guardian_id': str(guardian_id),
            'medical_records': None,
            'is_emergency': False,
            'created_at': datetime.utcnow()
        })
        patient_id = patient_result.inserted_id
        print(f"✓ Patient created with ID: {patient_id}")
    
    # Add demo medications
    print(f"\n💊 DEMO MEDICATIONS")
    demo_medications = [
        {
            'name': 'Aspirin',
            'dosage': '1 tablet',
            'time_of_day': 'Morning',
            'timing': '08:00',
            'stock': 30
        },
        {
            'name': 'Metformin',
            'dosage': '2 tablets',
            'time_of_day': 'Afternoon',
            'timing': '14:00',
            'stock': 45
        },
        {
            'name': 'Lisinopril',
            'dosage': '1 tablet',
            'time_of_day': 'Evening',
            'timing': '18:00',
            'stock': 30
        },
        {
            'name': 'Melatonin',
            'dosage': '1 tablet',
            'time_of_day': 'Bedtime',
            'timing': '22:00',
            'stock': 60
        }
    ]
    
    # Clear existing medications for this patient
    db.medications.delete_many({'patient_id': str(patient_id)})
    
    for med in demo_medications:
        db.medications.insert_one({
            'patient_id': str(patient_id),
            'name': med['name'],
            'dosage': med['dosage'],
            'time_of_day': med['time_of_day'],
            'timing': med['timing'],
            'stock': med['stock'],
            'created_at': datetime.utcnow()
        })
        print(f"  ✓ {med['name']} - {med['dosage']} ({med['time_of_day']})")
    
    # Add demo vitals
    print(f"\n❤️ DEMO VITALS")
    now = datetime.utcnow()
    demo_vitals = [
        {'type': 'Heart Rate', 'value': 72, 'unit': 'bpm'},
        {'type': 'Blood Pressure', 'value': '120/80', 'unit': 'mmHg'},
        {'type': 'Temperature', 'value': 98.6, 'unit': '°F'},
        {'type': 'Oxygen Level', 'value': 98, 'unit': '%'}
    ]
    
    # Clear existing vitals for this patient
    db.vitals.delete_many({'patient_id': str(patient_id)})
    
    for vital in demo_vitals:
        db.vitals.insert_one({
            'patient_id': str(patient_id),
            'type': vital['type'],
            'value': vital['value'],
            'unit': vital['unit'],
            'timestamp': now - timedelta(hours=2)
        })
        print(f"  ✓ {vital['type']}: {vital['value']} {vital['unit']}")
    
    # Add demo appointments
    print(f"\n📅 DEMO APPOINTMENTS")
    
    # Clear existing appointments for this patient
    db.appointments.delete_many({'patient_id': str(patient_id)})
    
    demo_appointments = [
        {
            'doctor_name': 'Dr. Priya Singh',
            'specialty': 'Cardiology',
            'date': (now + timedelta(days=5)).strftime('%Y-%m-%d'),
            'time': '10:00'
        },
        {
            'doctor_name': 'Dr. Amit Patel',
            'specialty': 'Endocrinology',
            'date': (now + timedelta(days=10)).strftime('%Y-%m-%d'),
            'time': '14:30'
        },
        {
            'doctor_name': 'Dr. Neha Sharma',
            'specialty': 'General Checkup',
            'date': (now + timedelta(days=15)).strftime('%Y-%m-%d'),
            'time': '09:00'
        }
    ]
    
    for appt in demo_appointments:
        db.appointments.insert_one({
            'patient_id': str(patient_id),
            'doctor_name': appt['doctor_name'],
            'specialty': appt['specialty'],
            'date': appt['date'],
            'time': appt['time'],
            'created_at': now
        })
        print(f"  ✓ {appt['doctor_name']} ({appt['specialty']}) - {appt['date']} at {appt['time']}")
    
    # Add demo notifications
    print(f"\n📢 DEMO NOTIFICATIONS")
    
    # Clear existing notifications
    db.notifications.delete_many({'user_id': str(guardian_id)})
    
    demo_notifications = [
        "✓ Mr. Rajesh took his morning medications",
        "⚠️ Low stock alert: Aspirin has only 5 tablets left",
        "📅 Upcoming appointment: Cardiology with Dr. Priya Singh on Mar 5",
        "💊 Time for afternoon medication: Metformin"
    ]
    
    for i, notif in enumerate(demo_notifications):
        db.notifications.insert_one({
            'user_id': str(guardian_id),
            'message': notif,
            'timestamp': now - timedelta(days=len(demo_notifications)-i),
            'is_read': False
        })
        print(f"  ✓ {notif}")
    
    print("\n" + "=" * 60)
    print("✅ DEMO ACCOUNTS CREATED SUCCESSFULLY!")
    print("=" * 60)
    print("\n🔐 LOGIN CREDENTIALS FOR JUDGES:")
    print(f"\n  Guardian Account:")
    print(f"    Email: {guardian_email}")
    print(f"    Password: {guardian_password}")
    print(f"\n  Patient Account (if needed):")
    print(f"    Email: {patient_email}")
    print(f"    Password: {patient_password}")
    print("\n💡 The demo includes:")
    print("   • Sample patient profile (Mr. Rajesh Kumar)")
    print("   • 4 medications with different timings")
    print("   • Current vital signs")
    print("   • 3 upcoming appointments")
    print("   • Sample notifications")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        create_demo_accounts()
    except Exception as e:
        print(f"\n❌ Error creating demo accounts: {str(e)}")
        import traceback
        traceback.print_exc()
