from flask import Flask
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
from modals import create_vital, create_medication, create_appointment, create_task
from datetime import datetime
import random

load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI') or "mongodb://localhost:27017/seniorcare"
mongo = PyMongo(app)

def create_demo_data():
    with app.app_context():
        # 1. Find a target patient (the one we likely logged in as, or just the first one)
        patient = mongo.db.patients.find_one()
        
        if not patient:
            print("No patients found! Please signup a patient first.")
            return

        patient_id = str(patient['_id'])
        print(f"Creating data for patient: {patient['name']} ({patient_id})")

        # 2. Clear existing demo data for this patient (optional, but good for idempotency)
        mongo.db.vitals.delete_many({'patient_id': patient_id})
        mongo.db.medications.delete_many({'patient_id': patient_id})
        mongo.db.appointments.delete_many({'patient_id': patient_id})
        mongo.db.tasks.delete_many({'patient_id': patient_id})

        # 3. Create Vitals
        vitals_data = [
            ('Heart Rate', 72, 'bpm'),
            ('Blood Pressure', '120/80', 'mmHg'),
            ('Blood Sugar', 110, 'mg/dL'),
            ('Steps', 2500, 'steps'),
            ('SpO2', 98, '%')
        ]
        
        for v_type, val, unit in vitals_data:
            create_vital(mongo, patient_id, v_type, val, unit)
            print(f"Added Vital: {v_type}")

        # 4. Create Medications
        meds_data = [
            ('Lisinopril', '10mg', 'Morning', 30),
            ('Metformin', '500mg', 'After Lunch', 60),
            ('Atorvastatin', '20mg', 'Night', 15), # Low stock example
            ('Vitamin D3', '1000IU', 'Morning', 90)
        ]

        for name, dosage, time, stock in meds_data:
            create_medication(mongo, patient_id, name, dosage, time, stock)
            print(f"Added Med: {name}")

        # 5. Create Appointments
        appts_data = [
            ('Dr. Sarah Chen', 'Cardiologist', '2025-12-25', '10:00 AM'),
            ('Dr. Elizabeth Sterling', 'Physiotherapist', '2025-12-28', '02:30 PM'),
            ('Dr. Jonathan Hyde', 'Nutritionist', '2026-01-05', '09:00 AM')
        ]

        for doc, spec, date, time in appts_data:
            create_appointment(mongo, patient_id, doc, spec, date, time)
            print(f"Added Appt: {doc}")

        # 6. Create Daily Tasks
        tasks_data = [
            ('Morning Medication', 'Take Lisinopril and Vitamin D3'),
            ('Garden Walk', '15 mins light walking'),
            ('Blood Pressure Check', 'Log reading before lunch'),
            ('Afternoon Nap', '30 mins rest'),
            ('Hydration', 'Drink 2 glasses of water')
        ]

        for title, desc in tasks_data:
            create_task(mongo, patient_id, title, desc)
            print(f"Added Task: {title}")

        print("--- Demo Data Creation Complete ---")

if __name__ == "__main__":
    create_demo_data()
