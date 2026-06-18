// ── Wearable Simulation Logic ────────────────────────────────────────────────

const TOKEN = () => localStorage.getItem('shield_token');
let biometricInterval = null;

function updateHR(value) {
  document.getElementById('hrValue').textContent = `${value} BPM`;

  const status = document.getElementById('aiStatusText');
  const aiBox = document.getElementById('aiStatus');

  if (value >= 150) {
    status.textContent = '⚠️ CRITICAL: Heart rate dangerously high! Auto-alerting...';
    aiBox.className = 'ai-status danger';
    autoTriggerFromWearable('Extreme heart rate: ' + value + ' BPM');
  } else if (value >= 120) {
    status.textContent = '⚠️ Elevated heart rate detected. Monitoring closely...';
    aiBox.className = 'ai-status warn';
  } else {
    status.textContent = '✅ AI monitoring... all clear';
    aiBox.className = 'ai-status';
  }
}

function checkBiometrics() {
  const fall = document.getElementById('fallDetect').checked;
  const struggle = document.getElementById('struggleDetect').checked;
  const hr = parseInt(document.getElementById('heartRate').value);
  const status = document.getElementById('aiStatusText');
  const aiBox = document.getElementById('aiStatus');

  if (fall && struggle) {
    status.textContent = '🚨 CRITICAL: Fall + Struggle detected! Auto-alerting authorities...';
    aiBox.className = 'ai-status danger';
    autoTriggerFromWearable('Fall and struggle simultaneously detected');
  } else if (fall) {
    status.textContent = '⚠️ Fall detected! Are you okay?';
    aiBox.className = 'ai-status warn';
  } else if (struggle) {
    status.textContent = '⚠️ Struggle pattern detected. Monitoring...';
    aiBox.className = 'ai-status warn';
  }
}

async function autoTriggerFromWearable(reason) {
  clearInterval(biometricInterval);

  // Get location
  let lat = 28.6139, lng = 77.2090;
  try {
    const pos = await new Promise((res, rej) =>
      navigator.geolocation.getCurrentPosition(res, rej));
    lat = pos.coords.latitude;
    lng = pos.coords.longitude;
  } catch(e) {}

  try {
    const res = await fetch('/api/cases/trigger', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TOKEN()}`
      },
      body: JSON.stringify({
        lat, lng,
        trigger_type: 'wearable',
        heart_rate: parseInt(document.getElementById('heartRate').value),
        fall_detected: document.getElementById('fallDetect').checked,
        struggle_detected: document.getElementById('struggleDetect').checked
      })
    });

    const data = await res.json();
    document.getElementById('aiStatusText').textContent =
      `🚨 ALERT SENT! Case ID: ${data.case_id?.slice(-6)} — Authorities notified`;

  } catch(e) {
    console.error('Wearable alert failed:', e);
  }
}

async function sendWearableAlert() {
  const hr = parseInt(document.getElementById('heartRate').value);
  const fall = document.getElementById('fallDetect').checked;
  const struggle = document.getElementById('struggleDetect').checked;
  await autoTriggerFromWearable(`Manual wearable trigger — HR:${hr} Fall:${fall} Struggle:${struggle}`);
}
