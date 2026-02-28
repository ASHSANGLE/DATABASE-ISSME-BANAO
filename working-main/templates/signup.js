// ============================================================
//  GoldenSage – Patient Signup Logic
//  Connects HTML form to Supabase Auth + patients table
// ============================================================

// ⚠️ Make sure supabase-config.js is loaded BEFORE this file
// It should define: const supabase = window.supabase.createClient(URL, KEY)

document.addEventListener('DOMContentLoaded', () => {

  const form = document.querySelector('form');

  // Change form tag attributes in your HTML to:
  // <form id="patientForm">  (remove action and method)
  if (form) {
    form.id = 'patientForm';
    form.removeAttribute('action');
    form.removeAttribute('method');
  }

  document.getElementById('patientForm')?.addEventListener('submit', handleSignup);
});


// ── MAIN SIGNUP HANDLER ──────────────────────────────────────
async function handleSignup(e) {
  e.preventDefault();

  const btn = document.querySelector('.btn-submit');
  btn.disabled = true;
  btn.innerText = 'Registering...';

  try {

    // ── 1. COLLECT FORM DATA ───────────────────────────────
    const data = collectFormData();

    if (!data) {
      btn.disabled = false;
      btn.innerText = 'Complete Patient Signup';
      return;
    }

    // ── 2. SUPABASE AUTH – Create account ─────────────────
    const { data: authData, error: authError } = await supabaseClient.auth.signUp({
      email: data.email,
      password: data.password,
      options: {
        data: { full_name: data.name }   // stored in auth.users metadata
      }
    });

    if (authError) throw new Error('Auth Error: ' + authError.message);

    const userId = authData?.user?.id;

    // ── 3. UPLOAD PROFILE PHOTO (optional) ────────────────
    let photoUrl = null;
    const photoFile = document.getElementById('pImgUpload')?.files[0];
    if (photoFile && userId) {
      photoUrl = await uploadPhoto(photoFile, userId);
    }

    // ── 4. UPLOAD MEDICAL REPORTS (optional) ──────────────
    let reportUrls = [];
    const reportFiles = document.querySelector('input[type="file"][multiple]')?.files;
    if (reportFiles && reportFiles.length > 0 && userId) {
      reportUrls = await uploadReports(reportFiles, userId);
    }

    // ── 5. INSERT PATIENT RECORD ───────────────────────────
    const { error: dbError } = await supabaseClient.from('patients').insert([{
      user_id:            userId,
      name:               data.name,
      email:              data.email,
      phone:              data.phone,
      age:                data.age,
      gender:             data.gender,
      blood_group:        data.blood_group,
      primary_condition:  data.primary_condition,
      allergies:          data.allergies,
      condition_details:  data.condition_details,
      memory_conditions:  data.memory_conditions,   // array e.g. ["Alzheimer's","Dementia"]
      guardian_email:     data.guardian_email,
      guardian_phone:     data.guardian_phone,
      doctor_name:        data.doctor_name,
      doctor_phone:       data.doctor_phone,
      emergency_hotline:  data.emergency_hotline,
      neighbor_phone:     data.neighbor_phone,
      preferred_hospital: data.preferred_hospital,
      street_address:     data.street_address,
      area:               data.area,
      city:               data.city,
      state:              data.state,
      country:            data.country,
      pincode:            data.pincode,
      reminders:          data.reminders,           // array of reminder strings
      photo_url:          photoUrl,
      report_urls:        reportUrls,
    }]);

    if (dbError) throw new Error('Database Error: ' + dbError.message);

    // ── 6. SUCCESS ─────────────────────────────────────────
    showToast('✅ Patient registered successfully! Redirecting...', 'success');
    setTimeout(() => window.location.href = '/main', 2500);

  } catch (err) {
    console.error(err);
    showToast('❌ ' + err.message, 'error');
    btn.disabled = false;
    btn.innerText = 'Complete Patient Signup';
  }
}


// ── COLLECT ALL FORM FIELDS ──────────────────────────────────
function collectFormData() {
  const get = (name) => document.querySelector(`[name="${name}"]`)?.value?.trim() || '';

  const email    = get('email');
  const password = get('password');
  const name     = get('name');
  const phone    = get('phone');

  // Basic validation
  if (!name)     { showToast('⚠️ Patient name is required', 'error'); return null; }
  if (!email)    { showToast('⚠️ Patient email is required', 'error'); return null; }
  if (!password) { showToast('⚠️ Password is required', 'error'); return null; }
  if (password.length < 6) { showToast('⚠️ Password must be at least 6 characters', 'error'); return null; }

  // Gender (radio buttons)
  const genderEl = document.querySelector('input[name="g"]:checked');
  const gender = genderEl ? genderEl.parentElement.innerText.trim() : '';

  // Memory conditions (checkboxes)
  const memoryConditions = [];
  document.querySelectorAll('.checkbox-group input[type="checkbox"]:checked').forEach(cb => {
    memoryConditions.push(cb.parentElement.innerText.trim());
  });

  // Care Reminders (dynamic inputs)
  const reminders = [];
  document.querySelectorAll('#reminderList input').forEach(input => {
    if (input.value.trim()) reminders.push(input.value.trim());
  });

  // All inputs by position (fields without name attributes)
  const allInputs = document.querySelectorAll('input:not([type="file"]):not([type="radio"]):not([type="checkbox"])');
  // Map inputs by their label text
  const fieldMap = {};
  document.querySelectorAll('.form-group').forEach(group => {
    const label = group.querySelector('label')?.innerText?.replace(' *', '').trim();
    const input = group.querySelector('input, select, textarea');
    if (label && input && input.value) {
      fieldMap[label] = input.value.trim();
    }
  });

  return {
    name,
    email,
    password,
    phone,
    gender,
    age:                parseInt(fieldMap['Age']) || null,
    blood_group:        document.querySelector('select')?.value || '',
    primary_condition:  fieldMap['Primary Condition'] || '',
    allergies:          fieldMap['Allergies & Sensitivities'] || '',
    condition_details:  document.querySelectorAll('textarea')[1]?.value?.trim() || '',
    memory_conditions:  memoryConditions,
    guardian_email:     get('guardian_email'),
    guardian_phone:     fieldMap['Guardian Phone'] || '',
    doctor_name:        fieldMap["Primary Physician ( Doctor's name)"] || fieldMap['Primary Physician'] || '',
    doctor_phone:       fieldMap["Doctor's Phone Number"] || '',
    emergency_hotline:  fieldMap['Emergency Hotline'] || '',
    neighbor_phone:     fieldMap["Neighbor's Phone Number"] || '',
    preferred_hospital: fieldMap['Preferred Hospital'] || '',
    street_address:     fieldMap['House / Street / Apartment'] || '',
    area:               fieldMap['Area / Locality'] || '',
    city:               fieldMap['City'] || '',
    state:              fieldMap['State'] || '',
    country:            fieldMap['Country'] || '',
    pincode:            fieldMap['Pincode / ZIP'] || '',
    reminders,
  };
}


// ── UPLOAD PROFILE PHOTO ─────────────────────────────────────
async function uploadPhoto(file, userId) {
  try {
    const ext = file.name.split('.').pop();
    const path = `patients/${userId}/photo.${ext}`;

    const { error } = await supabaseClient.storage
      .from('patient-assets')          // 🪣 create this bucket in Supabase Storage
      .upload(path, file, { upsert: true });

    if (error) throw error;

    const { data } = supabaseClient.storage.from('patient-assets').getPublicUrl(path);
    return data.publicUrl;
  } catch (err) {
    console.warn('Photo upload failed:', err.message);
    return null;
  }
}


// ── UPLOAD MEDICAL REPORTS ───────────────────────────────────
async function uploadReports(files, userId) {
  const urls = [];
  for (const file of files) {
    try {
      const path = `patients/${userId}/reports/${Date.now()}_${file.name}`;
      const { error } = await supabaseClient.storage
        .from('patient-assets')         // 🪣 same bucket
        .upload(path, file, { upsert: true });

      if (error) throw error;

      const { data } = supabaseClient.storage.from('patient-assets').getPublicUrl(path);
      urls.push(data.publicUrl);
    } catch (err) {
      console.warn('Report upload failed:', err.message);
    }
  }
  return urls;
}


// ── TOAST NOTIFICATION ───────────────────────────────────────
function showToast(message, type = 'success') {
  // Remove existing toast
  document.getElementById('gs-toast')?.remove();

  const toast = document.createElement('div');
  toast.id = 'gs-toast';
  toast.innerText = message;
  toast.style.cssText = `
    position: fixed;
    bottom: 30px;
    right: 30px;
    padding: 16px 24px;
    border-radius: 14px;
    font-size: 15px;
    font-weight: 600;
    color: white;
    background: ${type === 'success' ? '#2f5d50' : '#ef4444'};
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    z-index: 9999;
    animation: slideIn 0.3s ease;
    max-width: 380px;
  `;

  // Add animation keyframes once
  if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.innerText = `@keyframes slideIn { from { opacity:0; transform: translateY(20px); } to { opacity:1; transform: translateY(0); } }`;
    document.head.appendChild(style);
  }

  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}