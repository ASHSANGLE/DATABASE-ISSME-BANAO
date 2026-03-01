# SOS Emergency Alert - Debugging Guide

## Overview
The SOS emergency alert feature sends an emergency notification to the patient's caretaker. An error dialog appears when the system fails to send this alert.

## Error: "Error Sending SOS"

### What was fixed:
1. **Enhanced Backend Logging** - The SOS endpoint now logs detailed debug information showing exactly where the process fails
2. **Improved Error Messages** - Server now returns detailed error descriptions instead of generic messages
3. **Better Frontend Error Handling** - The patient dashboard now displays the actual error message from the server
4. **Fixed Voice Assistant Fetch** - Added `credentials: 'same-origin'` to ensure cookies are sent with the request
5. **New Debug Endpoint** - Created `/feature/sos/debug` to diagnose system issues

## Quick Diagnosis

### Step 1: Check Your Authentication
Open browser Developer Tools (F12) and run:
```javascript
fetch('/feature/sos/debug').then(r => r.json()).then(console.log)
```

This will show:
- ✓ Whether you're logged in
- ✓ Your user role (should be "patient")
- ✓ Patient record found in database
- ✓ Required fields (name, guardian_id, phone)
- ✓ Twilio configuration status
- ✓ MongoDB connectivity

### Step 2: Check Console Logs
In your browser's Developer Console (F12), look for error messages when clicking SOS button. These should now show the actual error from the server.

### Step 3: Check Server Logs
When running Flask, look for log messages with emoji indicators:
- 🚨 - SOS event started
- ✓ - Step completed successfully
- ❌ - Error occurred
- ⚠️ - Warning (non-critical issue)
- 🔍 - Debug information

### Step 4: Common Issues and Fixes

#### Issue: "Not authenticated" or 401 error
**Cause:** You're not logged in or session expired
**Fix:** 
- Log out and log back in
- Clear browser cookies
- Try in a fresh incognito window

#### Issue: "Patient not found" or 404 error
**Cause:** Your patient record doesn't exist in the database
**Fix:**
- Check that your user was created as a patient (not guardian)
- Contact administrator to verify patient record exists

#### Issue: "Invalid patient ID format" or 400 error
**Cause:** Patient ID is corrupted or invalid
**Fix:**
- Clear browser cookies and log in again
- Try a different browser
- Contact administrator

#### Issue: "SOS trigger failed" with no details
**Cause:** One of these:
- Missing patient name in database
- Missing guardian_id association  
- MongoDB query failed
**Fix:**
- Check patient record has: name, email, guardian_id, phone
- Verify database connection is working
- Check MongoDB is running: `mongosh` command in terminal

#### Issue: SMS not sending (but alert shows success)
**Cause:** Twilio credentials missing or incorrect
**Fix:**
- Check .env file has: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
- Verify EMERGENCY_CONTACT_NUMBER and HOSPITAL_CONTACT_NUMBER are set
- Check Twilio account has SMS credits

## Testing the SOS System

### Method 1: Automated Debug Check
```javascript
// In browser console:
fetch('/feature/sos/debug').then(r => r.json()).then(d => {
  console.table(d);
  if (d.patient_found) console.log('✓ Patient record OK');
  if (d.user_authenticated) console.log('✓ Logged in');
  Object.entries(d.twilio_configured).forEach(([k,v]) => {
    console.log(`Twilio ${k}: ${v ? '✓' : '✗'}`);
  });
})
```

### Method 2: Manual SOS Trigger
1. Go to Patient Dashboard
2. Click the red SOS emergency button
3. Confirm the alert
4. Check console for error messages

### Method 3: Test SOS Endpoint Directly
```bash
# Get a session cookie first by logging in, then:
curl -X POST https://yourapp.com/feature/sos/trigger \
  -H "Content-Type: application/json" \
  -b "session=your_session_cookie" \
```

## Database Schema Validation

Patient record MUST have these fields:
```javascript
{
  _id: ObjectId,
  name: String,           // Required for SOS
  email: String,
  phone: String,          // Required for SMS
  password: String hash,
  guardian_id: ObjectId,  // Required for notification
  is_emergency: Boolean,
  created_at: Date
}
```

Guardian record MUST have:
```javascript
{
  _id: ObjectId,
  email: String,
  password: String hash,
  name: String,  // Optional but recommended
  created_at: Date
}
```

## Code Changes Made

### Backend (app.py)
- Enhanced `sos_trigger()` with detailed logging and error handling
- Added `sos_debug()` endpoint for diagnostics
- All database operations now have try-catch with specific error messages

### Frontend (patient-dashboard.html)
- Updated `confirmSOS()` to show error details from server
- Added console logging for debugging

### Frontend (voice-assistant.html)
- Added `credentials: 'same-origin'` to fetch request
- Added error handling for network failures
- Now shows specific error messages

## Monitoring SOS Alerts

Check SOS alerts in MongoDB:
```javascript
db.sos_alerts.find().pretty()  // All alerts
db.sos_alerts.find({status: 'active'}).pretty()  // Active alerts
db.notifications.find({type: 'emergency_sos'}).pretty()  // SOS notifications
```

## Performance Considerations

The SOS feature includes:
1. **Database Operations** - 3 inserts/updates (alert, patient flag, notification)
2. **SMS Sending** - Up to 2 SMS messages via Twilio (async, non-blocking)
3. **Total Response Time** - Should be < 2 seconds

If slower, check:
- MongoDB performance
- Twilio API latency
- Network connectivity

## Emergency Fallback

If SOS fails, users are instructed to:
1. Call 112 (emergency services)
2. Click "Retry" button  
3. Contact administrator

## Support

For persistent issues:
1. Enable Flask debug mode: `app.run(debug=True)`
2. Collect browser console logs
3. Collect server logs with emoji indicators
4. Run `/feature/sos/debug` debug endpoint
5. Check MongoDB connection: `mongosh seniorcare`
6. Verify .env configuration

