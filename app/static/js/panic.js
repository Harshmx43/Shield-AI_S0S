// ── ShieldAI Panic Button Logic ──────────────────────────────────────────────

let clickCount = 0;
let clickTimer = null;
let holdTimer = null;
let mediaRecorder = null;
let audioChunks = [];
let activeCase = null;
let locationInterval = null;
let cancelTimer = null;
let cancelCountdown = null;

const TOKEN = () => localStorage.getItem('shield_token');

// ── Click Detection (3 rapid clicks) ─────────────────────────────────────────
function triggerPanic() {
  clickCount++;
  clearTimeout(clickTimer);

  if (clickCount >= 3) {
    clickCount = 0;
    activateShieldAI();
    return;
  }

  clickTimer = setTimeout(() => { clickCount = 0; }, 800);

  // Visual feedback
  const btn = document.getElementById('panicBtn');
  btn.style.transform = 'scale(0.95)';
  setTimeout(() => btn.style.transform = '', 150);
}

// Hold to trigger (2 seconds)
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('panicBtn');
  if (!btn) return;

  btn.addEventListener('mousedown', () => {
    holdTimer = setTimeout(() => activateShieldAI(), 2000);
  });
  btn.addEventListener('mouseup', () => clearTimeout(holdTimer));
  btn.addEventListener('touchstart', (e) => {
    e.preventDefault();
    holdTimer = setTimeout(() => activateShieldAI(), 2000);
  });
  btn.addEventListener('touchend', () => clearTimeout(holdTimer));
});

// ── Main Activation ───────────────────────────────────────────────────────────
async function activateShieldAI() {
  // Show cancel banner
  document.getElementById('cancelBanner').style.display = 'flex';
  document.getElementById('panicRing').classList.add('pulsing');
  document.getElementById('statusText').textContent = '🚨 Alert Active — Recording...';
  document.getElementById('statusBar').className = 'status-bar danger';

  startCancelCountdown();
  await startRecording();
  await captureLocation();
}

// ── Cancel Countdown ──────────────────────────────────────────────────────────
function startCancelCountdown() {
  let seconds = 10;
  document.getElementById('countdown').textContent = seconds;

  cancelCountdown = setInterval(() => {
    seconds--;
    document.getElementById('countdown').textContent = seconds;
    if (seconds <= 0) {
      clearInterval(cancelCountdown);
      sendAlert();
    }
  }, 1000);
}

function cancelAlert() {
  clearInterval(cancelCountdown);
  stopRecording();
  resetUI();

  if (activeCase) {
    shieldSocket.emit('cancel_alert', { case_id: activeCase });
    activeCase = null;
  }
}

// ── Audio Recording ───────────────────────────────────────────────────────────
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.start();

    document.getElementById('recordingIndicator').style.display = 'flex';

    // Stop after 30 seconds
    setTimeout(() => {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }
    }, 30000);

  } catch (err) {
    console.error('Mic access denied:', err);
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  document.getElementById('recordingIndicator').style.display = 'none';
}

// ── Location Capture ──────────────────────────────────────────────────────────
let currentLat = null;
let currentLng = null;

async function captureLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      console.warn('Geolocation not supported');
      resolve();
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        currentLat = pos.coords.latitude;
        currentLng = pos.coords.longitude;
        console.log('📍 GPS captured:', currentLat, currentLng);
        resolve();
      },
      (err) => {
        console.warn('GPS error:', err.message);
        // Try IP-based location as fallback
        fetch('https://ipapi.co/json/')
          .then(r => r.json())
          .then(data => {
            if (data.latitude && data.longitude) {
              currentLat = data.latitude;
              currentLng = data.longitude;
              console.log('📍 IP location used:', currentLat, currentLng);
            }
            resolve();
          })
          .catch(() => resolve());
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  });
}

// ── Send Alert to Backend ─────────────────────────────────────────────────────
async function sendAlert() {
  clearInterval(cancelCountdown);

  let audioBase64 = '';
  if (audioChunks.length > 0) {
    const blob = new Blob(audioChunks, { type: 'audio/webm' });
    audioBase64 = await blobToBase64(blob);
  }

  try {
    const res = await fetch('/api/cases/trigger', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TOKEN()}`
      },
      body: JSON.stringify({
        lat: currentLat || null,
        lng: currentLng || null,
        trigger_type: 'panic',
        audio_base64: audioBase64
      })
    });

    const data = await res.json();
    activeCase = data.case_id;

    // Start live location updates
    startLocationUpdates();

    document.getElementById('cancelBanner').style.display = 'none';
    showActiveAlert(data.case_id);

  } catch(e) {
    console.error('Alert failed:', e);
  }
}

// ── Live Location Updates ─────────────────────────────────────────────────────
function startLocationUpdates() {
  locationInterval = setInterval(() => {
    navigator.geolocation.getCurrentPosition((pos) => {
      fetch('/api/location/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${TOKEN()}`
        },
        body: JSON.stringify({
          case_id: activeCase,
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        })
      });
    });
  }, 10000);
}

// ── UI Helpers ────────────────────────────────────────────────────────────────
function showActiveAlert(caseId) {
  document.getElementById('statusText').textContent = `🚨 HELP IS COMING — Case #${caseId.slice(-6)}`;
  document.getElementById('panicBtn').innerHTML = `
    <i class="fas fa-check-circle"></i>
    <span>Alert Sent</span>
    <small>Authorities notified</small>
  `;
  document.getElementById('panicBtn').classList.add('sent');
}

function resetUI() {
  document.getElementById('cancelBanner').style.display = 'none';
  document.getElementById('panicRing').classList.remove('pulsing');
  document.getElementById('recordingIndicator').style.display = 'none';
  document.getElementById('statusText').textContent = 'You are safe';
  document.getElementById('statusBar').className = 'status-bar';
  clearInterval(locationInterval);
}

function blobToBase64(blob) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(',')[1]);
    reader.readAsDataURL(blob);
  });
}

function shareLocation() {
  navigator.geolocation.getCurrentPosition((pos) => {
    const url = `https://maps.google.com/?q=${pos.coords.latitude},${pos.coords.longitude}`;
    navigator.clipboard.writeText(url).then(() => alert('Location link copied!'));
  });
}
