import os
import sys

# Add working-main to python path to import app logic
sys.path.append(r"c:\Users\HIMU\OneDrive\Desktop\1\DATABASE ISSME BANAO\working-main")

from app import app, mongo

def remove_duplicate_vital():
    with app.app_context():
        # Find all patients to check their vitals
        patients = list(mongo.db.patients.find())
        for patient in patients:
            patient_id = str(patient['_id'])
            
            # Get their vitals sorted by timestamp descending
            vitals = list(mongo.db.vitals.find({'patient_id': patient_id}).sort('timestamp', -1))
            
            # Keep track of which types we've seen
            seen_types = set()
            duplicates_removed = 0
            
            # If we're keeping the most recent 10 (as in the dashboard query)
            for vital in vitals:
                v_type = vital.get('type')
                if v_type in seen_types:
                    # Duplicate found! Let's delete it.
                    print(f"Removing duplicate vital: {v_type} ({vital.get('value')} {vital.get('unit')}) for patient {patient.get('name')}")
                    mongo.db.vitals.delete_one({'_id': vital['_id']})
                    duplicates_removed += 1
                else:
                    seen_types.add(v_type)
            
            if duplicates_removed > 0:
                 print(f"Removed {duplicates_removed} duplicate vitals for {patient.get('name')}")

if __name__ == '__main__':
    print("Connecting to MongoDB to remove duplicates...")
    remove_duplicate_vital()
    print("Done.")
