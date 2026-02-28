// Medication Reminder - Senior-Friendly JavaScript

document.addEventListener('DOMContentLoaded', initializeApp);

let reminderInterval;
let notificationPermissionGranted = false;
let currentAlarm = null;
let alarmAudioInterval = null;
let alarmAudio = null;
let currentTimePicker = {
    targetInput: null,
    hour: 8,
    minute: 0
};

// ==================== INITIALIZATION ====================

function initializeApp() {
    updateTimeDisplay();
    setInterval(updateTimeDisplay, 1000); // Update time every second
    
    loadAllData();
    
    // Check notification permission status first
    if (Notification.permission === "granted") {
        notificationPermissionGranted = true;
    }
    
    // Only request permission if not already asked
    requestNotificationPermission();
    startReminderCheck();
    updateSummary();
}

// ==================== TIME DISPLAY ====================

function updateTimeDisplay() {
    const now = new Date();
    const timeElement = document.getElementById('currentTime');
    const dateElement = document.getElementById('currentDate');
    
    if (timeElement) {
        const timeString = now.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit',
            hour12: true 
        });
        timeElement.textContent = timeString;
    }
    
    if (dateElement) {
        const dateString = now.toLocaleDateString('en-US', { 
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        dateElement.textContent = dateString;
    }
}

// ==================== NOTIFICATION PERMISSION ====================

function requestNotificationPermission() {
    if (!("Notification" in window)) {
        console.warn("This browser does not support desktop notifications.");
        return;
    }
    
    // Check if permission was already requested (stored in localStorage)
    const permissionRequested = localStorage.getItem('notificationPermissionRequested');
    
    // Only ask if permission is default AND we haven't asked before
    if (Notification.permission === "default" && !permissionRequested) {
        Notification.requestPermission().then(permission => {
            notificationPermissionGranted = (permission === "granted");
            // Store that we've requested permission (regardless of answer)
            localStorage.setItem('notificationPermissionRequested', 'true');
            if (notificationPermissionGranted) {
                showNotification("Medication Reminder", "You will now receive medication reminders!");
            }
        });
    } else if (Notification.permission === "granted") {
        notificationPermissionGranted = true;
    } else if (Notification.permission === "denied") {
        // Permission was denied, don't ask again
        localStorage.setItem('notificationPermissionRequested', 'true');
    }
}

// ==================== REMINDER CHECKING ====================

function startReminderCheck() {
    // Check every 30 seconds for more accurate reminders
    reminderInterval = setInterval(checkReminders, 30000);
    console.log("Reminder check started - checking every 30 seconds");
}

function checkReminders() {
    // Check if alarm is snoozed and still within snooze time
    if (currentAlarm && currentAlarm.snoozed && currentAlarm.snoozeUntil) {
        if (new Date() < currentAlarm.snoozeUntil) {
            return; // Still in snooze period
        } else {
            // Snooze period expired, allow new alarms
            currentAlarm = null;
        }
    }
    
    // Don't show new alarm if one is already active (not snoozed)
    if (currentAlarm && !currentAlarm.snoozed) {
        return;
    }
    
    const now = new Date();
    const currentTime = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
    });
    
    const data = getStoredData();
    if (!data) return;
    
    const allDoses = [
        ...(data.morning || []),
        ...(data.afternoon || []),
        ...(data.evening || []),
        ...(data.bedtime || [])
    ];
    
    allDoses.forEach(dose => {
        // Check if time matches, medication is not taken, and not already notified today
        // Also check that we're not showing an alarm for this medication already
        if (dose.time === currentTime && !dose.taken && !dose.notified) {
            // Don't trigger if we already have an active alarm for this medication
            if (currentAlarm && currentAlarm.name === dose.name) {
                return;
            }
            
            const patientName = data.patientName || 'Patient';
            const medicationInfo = {
                name: dose.name || 'Medication',
                dosage: dose.dosage || '',
                notes: dose.notes || '',
                patientName: patientName
            };
            
            // Show visible and audible alarm
            showVisibleAlarm(medicationInfo);
            
            // Also show browser notification
            if (notificationPermissionGranted) {
                const notificationTitle = `💊 Medication Reminder for ${patientName}`;
                const notificationBody = `Time to take: ${dose.name}\nDosage: ${dose.dosage}${dose.notes ? '\nNote: ' + dose.notes : ''}`;
                showNotification(notificationTitle, notificationBody);
            }
            
            // Mark as notified to prevent duplicate notifications
            dose.notified = true;
            saveAllData();
            
            console.log(`Reminder sent for ${dose.name} at ${currentTime}`);
        }
    });
}

// ==================== VISIBLE ALARM FUNCTIONALITY ====================

function showVisibleAlarm(medicationInfo) {
    // Store current alarm info
    currentAlarm = {
        ...medicationInfo,
        snoozed: false,
        snoozeUntil: null
    };
    
    // Show the alarm banner
    const alarmBanner = document.getElementById('alarmBanner');
    const alarmMessage = document.getElementById('alarmMessage');
    
    if (alarmBanner && alarmMessage) {
        // Build the message
        let message = `It's time to take your medication!\n\n`;
        message += `💊 <strong>${medicationInfo.name}</strong>\n`;
        if (medicationInfo.dosage) {
            message += `📏 Dosage: ${medicationInfo.dosage}\n`;
        }
        if (medicationInfo.notes) {
            message += `📝 Note: ${medicationInfo.notes}`;
        }
        
        alarmMessage.innerHTML = message.replace(/\n/g, '<br>');
        alarmBanner.classList.remove('hidden');
        alarmBanner.classList.add('flashing');
        
        // Add class to body for styling
        document.body.classList.add('alarm-active');
        
        // Scroll to top to show alarm
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Start playing alarm sound repeatedly
        startAlarmSound();
    }
}

function startAlarmSound() {
    // Stop any existing alarm
    stopAlarmSound();
    
    // Play immediately
    playAlarmSound();
    
    // Then play every 3 seconds until dismissed
    alarmAudioInterval = setInterval(() => {
        playAlarmSound();
    }, 3000);
}

function stopAlarmSound() {
    if (alarmAudioInterval) {
        clearInterval(alarmAudioInterval);
        alarmAudioInterval = null;
    }
    if (alarmAudio) {
        alarmAudio.pause();
        alarmAudio.currentTime = 0;
        alarmAudio = null;
    }
}

function dismissAlarm() {
    const alarmBanner = document.getElementById('alarmBanner');
    if (alarmBanner) {
        alarmBanner.classList.add('hidden');
        alarmBanner.classList.remove('flashing');
    }
    
    // Remove body class
    document.body.classList.remove('alarm-active');
    
    stopAlarmSound();
    
    // Mark the medication as taken in the data
    if (currentAlarm && currentAlarm.name) {
        markMedicationAsTakenInData(currentAlarm.name);
    }
    
    currentAlarm = null;
}

function markMedicationAsTakenInData(medicationName) {
    const data = getStoredData();
    if (!data) return;
    
    let found = false;
    
    // Search through all sections and mark as taken
    ['morning', 'afternoon', 'evening', 'bedtime'].forEach(section => {
        if (data[section]) {
            data[section].forEach(med => {
                if (med.name === medicationName && !med.taken) {
                    med.taken = true;
                    med.notified = true; // Also mark as notified to prevent re-triggering
                    found = true;
                }
            });
        }
    });
    
    if (found) {
        // Save the updated data
        localStorage.setItem('medicationReminderData', JSON.stringify(data));
        
        // Update the UI to reflect the change
        updateMedicationCheckboxInUI(medicationName, true);
        updateSummary();
    }
}

function updateMedicationCheckboxInUI(medicationName, checked) {
    // Find all medication items and update the checkbox if name matches
    const allMedItems = document.querySelectorAll('.med-item');
    allMedItems.forEach(item => {
        const nameInput = item.querySelector('.med-name');
        if (nameInput && nameInput.value === medicationName) {
            const checkbox = item.querySelector('.med-taken');
            if (checkbox) {
                checkbox.checked = checked;
                if (checked) {
                    item.classList.add('taken');
                } else {
                    item.classList.remove('taken');
                }
            }
        }
    });
}

function snoozeAlarm() {
    if (!currentAlarm) return;
    
    // Hide alarm banner
    const alarmBanner = document.getElementById('alarmBanner');
    if (alarmBanner) {
        alarmBanner.classList.add('hidden');
        alarmBanner.classList.remove('flashing');
    }
    
    // Remove body class
    document.body.classList.remove('alarm-active');
    
    stopAlarmSound();
    
    // Set snooze for 5 minutes
    currentAlarm.snoozed = true;
    currentAlarm.snoozeUntil = new Date(Date.now() + 5 * 60 * 1000);
    
    // Show the alarm again after 5 minutes
    setTimeout(() => {
        if (currentAlarm && currentAlarm.snoozed) {
            currentAlarm.snoozed = false;
            showVisibleAlarm(currentAlarm);
        }
    }, 5 * 60 * 1000);
    
    alert("⏰ Alarm snoozed for 5 minutes. You will be reminded again soon.");
}

// ==================== AUDIO FUNCTIONALITY ====================

function playAlarmSound() {
    try {
        // Stop previous audio if playing
        if (alarmAudio) {
            alarmAudio.pause();
            alarmAudio.currentTime = 0;
        }
        
        alarmAudio = new Audio('alarm.mp3');
        alarmAudio.volume = 0.8; // Higher volume for visibility
        alarmAudio.play().catch(e => {
            console.warn("Could not play sound:", e);
        });
    } catch (error) {
        console.warn("Audio file not found or error playing sound:", error);
    }
}

// ==================== NOTIFICATIONS ====================

function showNotification(title, body) {
    if (Notification.permission === "granted") {
        const options = {
            body: body,
            icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">💊</text></svg>',
            badge: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">💊</text></svg>',
            tag: 'medication-reminder',
            requireInteraction: true, // Keep notification visible until user interacts
            vibrate: [200, 100, 200] // Vibrate pattern (if supported)
        };
        
        try {
            new Notification(title, options);
        } catch (error) {
            console.error("Error creating notification:", error);
        }
    }
}

// ==================== MEDICATION MANAGEMENT ====================

function addMedication(timeOfDay) {
    const listContainer = document.getElementById(timeOfDay + 'List');
    if (!listContainer) return;
    
    const medId = Date.now() + Math.random(); // Unique ID
    const medItem = document.createElement('div');
    medItem.className = 'med-item';
    medItem.id = 'med-' + medId;
    
    medItem.innerHTML = `
        <div class="med-item-row">
            <label>⏰ Time:</label>
            <button type="button" class="time-input-btn" onclick="openTimePicker(this, '08:00')">
                <span class="time-display-text">08:00</span>
                <span>🕐</span>
            </button>
            <input type="hidden" class="med-time" value="08:00" onchange="saveAllData()">
        </div>
        <div class="med-item-row">
            <label>💊 Medication:</label>
            <input type="text" class="med-name" placeholder="Enter medication name" onchange="saveAllData()">
        </div>
        <div class="med-item-row">
            <label>📏 Dosage:</label>
            <input type="text" class="med-dosage" placeholder="e.g., 1 pill, 2 tablets" onchange="saveAllData()">
        </div>
        <div class="med-item-row">
            <label>📝 Notes:</label>
            <input type="text" class="med-notes" placeholder="e.g., with food, before meal" onchange="saveAllData()">
        </div>
        <div class="taken-checkbox-container">
            <input type="checkbox" class="taken-checkbox med-taken" id="taken-${medId}" onchange="markAsTaken(this); saveAllData();">
            <label for="taken-${medId}">✅ I have taken this medication</label>
        </div>
        <button class="delete-btn" onclick="deleteMedication('${medId}')">🗑️ Remove Medication</button>
    `;
    
    listContainer.appendChild(medItem);
    saveAllData();
    updateSummary();
}

function deleteMedication(medId) {
    if (confirm("Are you sure you want to remove this medication from your schedule?")) {
        const medItem = document.getElementById('med-' + medId);
        if (medItem) {
            medItem.remove();
            saveAllData();
            updateSummary();
            
            // Show delete confirmation message
            showDeleteConfirmation();
        }
    }
}

function showDeleteConfirmation() {
    const confirmation = document.getElementById('deleteConfirmation');
    if (confirmation) {
        confirmation.classList.remove('hidden');
        
        // Hide after 3 seconds
        setTimeout(() => {
            confirmation.classList.add('hidden');
        }, 3000);
    }
}

function markAsTaken(checkbox) {
    const medItem = checkbox.closest('.med-item');
    if (checkbox.checked) {
        medItem.classList.add('taken');
        
        // If alarm is showing and this medication matches, dismiss it
        if (currentAlarm) {
            const nameInput = medItem.querySelector('.med-name');
            if (nameInput && nameInput.value === currentAlarm.name) {
                dismissAlarm();
            }
        }
    } else {
        medItem.classList.remove('taken');
    }
    updateSummary();
}

// ==================== DATA STORAGE ====================

function saveAllData() {
    const data = {
        patientName: document.getElementById('patientName').value || '',
        morning: getSectionData('morningList'),
        afternoon: getSectionData('afternoonList'),
        evening: getSectionData('eveningList'),
        bedtime: getSectionData('bedtimeList')
    };
    
    localStorage.setItem('medicationReminderData', JSON.stringify(data));
    updateSummary();
    
    // Show confirmation message
    showSaveConfirmation();
}

function showSaveConfirmation() {
    const confirmation = document.getElementById('saveConfirmation');
    if (confirmation) {
        confirmation.classList.remove('hidden');
        
        // Hide after 3 seconds
        setTimeout(() => {
            confirmation.classList.add('hidden');
        }, 3000);
    }
}

function getSectionData(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return [];
    
    const medItems = section.querySelectorAll('.med-item');
    const sectionData = [];
    
    medItems.forEach(item => {
        const timeInput = item.querySelector('.med-time');
        const nameInput = item.querySelector('.med-name');
        const dosageInput = item.querySelector('.med-dosage');
        const notesInput = item.querySelector('.med-notes');
        const takenCheckbox = item.querySelector('.med-taken');
        
        sectionData.push({
            time: timeInput ? timeInput.value : '',
            name: nameInput ? nameInput.value : '',
            dosage: dosageInput ? dosageInput.value : '',
            notes: notesInput ? notesInput.value : '',
            taken: takenCheckbox ? takenCheckbox.checked : false,
            notified: false
        });
    });
    
    return sectionData;
}

function loadAllData() {
    const storedData = localStorage.getItem('medicationReminderData');
    if (!storedData) {
        // Show empty state messages
        showEmptyState('morningList');
        showEmptyState('afternoonList');
        showEmptyState('eveningList');
        showEmptyState('bedtimeList');
        return;
    }
    
    const data = JSON.parse(storedData);
    
    // Load patient name
    if (document.getElementById('patientName')) {
        document.getElementById('patientName').value = data.patientName || '';
    }
    
    // Load each section
    loadSectionData('morningList', data.morning || []);
    loadSectionData('afternoonList', data.afternoon || []);
    loadSectionData('eveningList', data.evening || []);
    loadSectionData('bedtimeList', data.bedtime || []);
    
    updateSummary();
}

function loadSectionData(sectionId, data) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    
    section.innerHTML = '';
    
    if (data.length === 0) {
        showEmptyState(sectionId);
        return;
    }
    
    data.forEach((item, index) => {
        const medId = Date.now() + index;
        const medItem = document.createElement('div');
        medItem.className = 'med-item';
        if (item.taken) {
            medItem.classList.add('taken');
        }
        medItem.id = 'med-' + medId;
        
        const timeValue = item.time || '08:00';
        medItem.innerHTML = `
            <div class="med-item-row">
                <label>⏰ Time:</label>
                <button type="button" class="time-input-btn" onclick="openTimePicker(this, '${timeValue}')">
                    <span class="time-display-text">${timeValue}</span>
                    <span>🕐</span>
                </button>
                <input type="hidden" class="med-time" value="${timeValue}" onchange="saveAllData()">
            </div>
            <div class="med-item-row">
                <label>💊 Medication:</label>
                <input type="text" class="med-name" value="${escapeHtml(item.name || '')}" placeholder="Enter medication name" onchange="saveAllData()">
            </div>
            <div class="med-item-row">
                <label>📏 Dosage:</label>
                <input type="text" class="med-dosage" value="${escapeHtml(item.dosage || '')}" placeholder="e.g., 1 pill, 2 tablets" onchange="saveAllData()">
            </div>
            <div class="med-item-row">
                <label>📝 Notes:</label>
                <input type="text" class="med-notes" value="${escapeHtml(item.notes || '')}" placeholder="e.g., with food, before meal" onchange="saveAllData()">
            </div>
            <div class="taken-checkbox-container">
                <input type="checkbox" class="taken-checkbox med-taken" id="taken-${medId}" ${item.taken ? 'checked' : ''} onchange="markAsTaken(this); saveAllData();">
                <label for="taken-${medId}">✅ I have taken this medication</label>
            </div>
            <button class="delete-btn" onclick="deleteMedication('${medId}')">🗑️ Remove Medication</button>
        `;
        
        section.appendChild(medItem);
    });
}

function showEmptyState(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    
    const timeOfDay = sectionId.replace('List', '');
    const timeLabels = {
        morning: '🌅 Morning',
        afternoon: '☀️ Afternoon',
        evening: '🌙 Evening',
        bedtime: '🌛 Bedtime'
    };
    
    section.innerHTML = `<div class="empty-state">No ${timeLabels[timeOfDay] || timeOfDay} medications added yet. Click "Add Medication" to get started.</div>`;
}

// ==================== SUMMARY STATISTICS ====================

function updateSummary() {
    const data = getStoredData();
    if (!data) {
        document.getElementById('totalMeds').textContent = '0';
        document.getElementById('takenMeds').textContent = '0';
        document.getElementById('pendingMeds').textContent = '0';
        return;
    }
    
    const allMeds = [
        ...(data.morning || []),
        ...(data.afternoon || []),
        ...(data.evening || []),
        ...(data.bedtime || [])
    ];
    
    const total = allMeds.length;
    const taken = allMeds.filter(med => med.taken).length;
    const pending = total - taken;
    
    document.getElementById('totalMeds').textContent = total;
    document.getElementById('takenMeds').textContent = taken;
    document.getElementById('pendingMeds').textContent = pending;
}

function getStoredData() {
    const storedData = localStorage.getItem('medicationReminderData');
    return storedData ? JSON.parse(storedData) : null;
}

// ==================== UTILITY FUNCTIONS ====================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function resetDailyCheckmarks() {
    if (confirm('Are you sure you want to reset all checkmarks for a new day? This will mark all medications as not taken.')) {
        const checkboxes = document.querySelectorAll('.med-taken');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            const medItem = checkbox.closest('.med-item');
            if (medItem) {
                medItem.classList.remove('taken');
            }
        });
        
        // Reset notified flags
        const data = getStoredData();
        if (data) {
            ['morning', 'afternoon', 'evening', 'bedtime'].forEach(section => {
                if (data[section]) {
                    data[section].forEach(med => {
                        med.taken = false;
                        med.notified = false;
                    });
                }
            });
            localStorage.setItem('medicationReminderData', JSON.stringify(data));
        }
        
        saveAllData();
        updateSummary();
        alert('✅ All checkmarks have been reset for the new day!');
    }
}

function testReminder() {
    // Test both visible and audible alarm
    const testMedication = {
        name: "Test Medication",
        dosage: "1 pill",
        notes: "This is a test reminder",
        patientName: document.getElementById('patientName').value || 'Test Patient'
    };
    
    showVisibleAlarm(testMedication);
    
    // Only request permission if not already granted or denied
    if (Notification.permission === "granted") {
        showNotification("Test Reminder", "This is a test notification. Your medication reminders are working correctly!");
    } else if (Notification.permission === "default") {
        // Only ask if we haven't asked before
        const permissionRequested = localStorage.getItem('notificationPermissionRequested');
        if (!permissionRequested) {
            requestNotificationPermission();
        }
    }
    
    // Auto-dismiss test alarm after 10 seconds
    setTimeout(() => {
        if (currentAlarm && currentAlarm.name === "Test Medication") {
            dismissAlarm();
        }
    }, 10000);
}

// ==================== TIME PICKER FUNCTIONS ====================

function openTimePicker(button, currentTime) {
    // Parse current time
    const timeParts = currentTime.split(':');
    const hour = parseInt(timeParts[0]) || 8;
    const minute = parseInt(timeParts[1]) || 0;
    
    // Store the target button and hidden input
    const medItem = button.closest('.med-item');
    const hiddenInput = medItem.querySelector('.med-time');
    
    currentTimePicker = {
        targetButton: button,
        targetInput: hiddenInput,
        hour: hour,
        minute: minute
    };
    
    // Update display
    updateTimePickerDisplay();
    
    // Show modal
    const modal = document.getElementById('timePickerModal');
    if (modal) {
        modal.classList.remove('hidden');
        // Prevent body scroll when modal is open
        document.body.classList.add('time-picker-open');
        // Scroll modal to top
        modal.scrollTop = 0;
    }
}

function closeTimePicker() {
    const modal = document.getElementById('timePickerModal');
    if (modal) {
        modal.classList.add('hidden');
        // Re-enable body scroll when modal is closed
        document.body.classList.remove('time-picker-open');
    }
    currentTimePicker = {
        targetInput: null,
        hour: 8,
        minute: 0
    };
}

function adjustTime(type, amount) {
    if (type === 'hour') {
        currentTimePicker.hour += amount;
        if (currentTimePicker.hour < 0) {
            currentTimePicker.hour = 23;
        } else if (currentTimePicker.hour > 23) {
            currentTimePicker.hour = 0;
        }
    } else if (type === 'minute') {
        currentTimePicker.minute += amount;
        if (currentTimePicker.minute < 0) {
            currentTimePicker.minute = 60 + currentTimePicker.minute;
            currentTimePicker.hour = (currentTimePicker.hour - 1 + 24) % 24;
        } else if (currentTimePicker.minute >= 60) {
            currentTimePicker.minute = currentTimePicker.minute - 60;
            currentTimePicker.hour = (currentTimePicker.hour + 1) % 24;
        }
    }
    
    updateTimePickerDisplay();
}

function setPresetTime(time) {
    const timeParts = time.split(':');
    currentTimePicker.hour = parseInt(timeParts[0]);
    currentTimePicker.minute = parseInt(timeParts[1]);
    updateTimePickerDisplay();
}

function updateTimePickerDisplay() {
    // Format hour and minute with leading zeros
    const hourStr = String(currentTimePicker.hour).padStart(2, '0');
    const minuteStr = String(currentTimePicker.minute).padStart(2, '0');
    const timeStr = `${hourStr}:${minuteStr}`;
    
    // Calculate 12-hour format
    let hour12 = currentTimePicker.hour;
    const period = hour12 >= 12 ? 'PM' : 'AM';
    if (hour12 === 0) {
        hour12 = 12;
    } else if (hour12 > 12) {
        hour12 = hour12 - 12;
    }
    const timeStr12h = `${hour12}:${minuteStr} ${period}`;
    
    // Update large 24-hour display
    const timeDisplay = document.getElementById('timeDisplayLarge');
    if (timeDisplay) {
        timeDisplay.textContent = timeStr;
    }
    
    // Update 12-hour display
    const timeDisplay12h = document.getElementById('timeDisplay12h');
    if (timeDisplay12h) {
        timeDisplay12h.textContent = timeStr12h;
    }
    
    // Update hour and minute values
    const hourValue = document.getElementById('hourValue');
    const minuteValue = document.getElementById('minuteValue');
    if (hourValue) {
        hourValue.textContent = hourStr;
    }
    if (minuteValue) {
        minuteValue.textContent = minuteStr;
    }
}

function confirmTimeSelection() {
    if (!currentTimePicker.targetInput || !currentTimePicker.targetButton) {
        closeTimePicker();
        return;
    }
    
    // Format time
    const hourStr = String(currentTimePicker.hour).padStart(2, '0');
    const minuteStr = String(currentTimePicker.minute).padStart(2, '0');
    const timeStr = `${hourStr}:${minuteStr}`;
    
    // Update hidden input
    currentTimePicker.targetInput.value = timeStr;
    
    // Update button display
    const displayText = currentTimePicker.targetButton.querySelector('.time-display-text');
    if (displayText) {
        displayText.textContent = timeStr;
    }
    
    // Save data
    saveAllData();
    
    // Close modal
    closeTimePicker();
}

