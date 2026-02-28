import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_api():
    session = requests.Session()
    
    timestamp = int(time.time())
    guardian_email = f"guardian_{timestamp}@test.com"
    patient_email = f"patient_{timestamp}@test.com"
    
    # 1. Signup Guardian
    print(f"--- 1. Signing up Guardian ({guardian_email}) ---")
    res = session.post(f"{BASE_URL}/signup/guardian", data={
        "email": guardian_email,
        "password": "password123"
    })
    
    # Check if redirect to dashboard happened (status 200 after follow redirect, or 302 if not following)
    # requests follows redirects by default
    if res.status_code == 200 and "dashboard" in res.url:
        print("✅ Guardian Signup & Login Successful")
    else:
        print(f"❌ Guardian Signup Failed: {res.status_code} - {res.url}")
        return

    # 2. Add Patient
    print(f"--- 2. Adding Patient ({patient_email}) ---")
    res = session.post(f"{BASE_URL}/signup-patient", data={
        "name": "Test Patient",
        "email": patient_email,
        "password": "password123",
        "phone": "555-0199"
    })
    
    if res.status_code == 200:
        print("✅ Patient Added Successfully")
    else:
        print(f"❌ Add Patient Failed: {res.status_code} - {res.text}")
        return

    # 3. Get Dashboard Data (to find patient ID)
    # The dashboard HTML contains the patient list, but we want the API data.
    # We can inspect the HTML or try to find the patient ID from the dashboard response if it was an API.
    # But /guardian-dashboard returns HTML.
    # However, we can use the pymongo direct access or... 
    # Wait, the dashboard HTML contains the ID in the <select> options!
    # Let's parse it simply.
    
    if 'value="' in res.text:
        # crude extraction of ObjectId
        try:
            # Look for <option value="ObjectId">
            # value="67a..."
            import re
            match = re.search(r'value="([a-f0-9]{24})"', res.text)
            if match:
                patient_id = match.group(1)
                print(f"✅ Found Patient ID: {patient_id}")
            else:
                print("❌ Could not find Patient ID in dashboard HTML")
                return
        except Exception as e:
            print(f"❌ Error parsing ID: {e}")
            return
    else:
        print("❌ Dashboard HTML does not contain patient list")
        return

    # 4. Fetch Guardian Dashboard Data API
    print(f"--- 3. Fetching Data for Patient {patient_id} ---")
    res = session.get(f"{BASE_URL}/api/guardian/dashboard-data/{patient_id}")
    if res.status_code == 200:
        data = res.json()
        print("✅ API Endpoint /api/guardian/dashboard-data SUCCESS")
        print(f"   - Vitals: {len(data['vitals'])}")
        print(f"   - Meds: {len(data['medications'])}")
        print(f"   - Tasks: {len(data['tasks'])}")
    else:
        print(f"❌ API Fetch Failed: {res.status_code} - {res.text}")
        return

    # 5. Book Appointment
    print("--- 4. Booking Appointment ---")
    book_data = {
        "patient_id": patient_id,
        "doctor_name": "Dr. API Test",
        "specialty": "Testing",
        "date": "2025-12-31",
        "time": "10:00 AM"
    }
    res = session.post(f"{BASE_URL}/api/appointment/book", json=book_data)
    if res.status_code == 200 and res.json().get('status') == 'success':
        print("✅ Appointment Booking SUCCESS")
    else:
        print(f"❌ Booking Failed: {res.status_code} - {res.text}")
        return

    # 6. Verify Appointment in Data
    print("--- 5. Verifying Appointment ---")
    res = session.get(f"{BASE_URL}/api/guardian/dashboard-data/{patient_id}")
    data = res.json()
    appointments = data.get('appointments', [])
    found = any(a['doctor_name'] == "Dr. API Test" for a in appointments)
    if found:
        print("✅ Appointment Verified in List")
    else:
        print("❌ Appointment NOT found in list")

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"❌ Script Error: {e}")
