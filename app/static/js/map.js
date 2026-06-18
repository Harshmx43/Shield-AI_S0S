// ── ShieldAI Authority Dashboard Map ─────────────────────────────────────────

let map;
let markers = {};
let cases = {};
const TOKEN = () => localStorage.getItem('shield_token');

const DANGER_COLORS = {
  CRITICAL: '#FF0000',
  HIGH: '#FF6600',
  MEDIUM: '#FFAA00',
  LOW: '#00CC44',
  ANALYZING: '#888888'
};

// ── Init Google Map ───────────────────────────────────────────────────────────
function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    center: { lat: 20.5937, lng: 78.9629 }, // India center
    zoom: 5,
    styles: [
      { elementType: 'geometry', stylers: [{ color: '#1a1a2e' }] },
      { elementType: 'labels.text.fill', stylers: [{ color: '#8ec3b9' }] },
      { featureType: 'water', stylers: [{ color: '#0d2137' }] },
      { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#304a7d' }] }
    ]
  });

  loadActiveCases();
  setupSocketListeners();
}

// ── Load Active Cases ─────────────────────────────────────────────────────────
async function loadActiveCases() {
  try {
    const res = await fetch('/api/cases/active', {
      headers: { 'Authorization': `Bearer ${TOKEN()}` }
    });
    const data = await res.json();
    data.forEach(addCaseToMap);
    updateStats(data);
  } catch(e) {
    console.error('Failed to load cases:', e);
  }
}

// ── Add Case to Map + Sidebar ─────────────────────────────────────────────────
function addCaseToMap(caseData) {
  const id = caseData._id;
  cases[id] = caseData;

  const color = DANGER_COLORS[caseData.danger_level] || '#888';
  const lat = caseData.location.lat;
  const lng = caseData.location.lng;

  // Pulsing marker
  const marker = new google.maps.Marker({
    position: { lat, lng },
    map,
    title: caseData.victim_name,
    icon: {
      path: google.maps.SymbolPath.CIRCLE,
      scale: caseData.danger_level === 'CRITICAL' ? 16 : 12,
      fillColor: color,
      fillOpacity: 0.9,
      strokeColor: '#fff',
      strokeWeight: 2
    },
    animation: caseData.danger_level === 'CRITICAL' ? google.maps.Animation.BOUNCE : null
  });

  marker.addListener('click', () => openCasePanel(id));
  markers[id] = marker;

  // Add to sidebar
  addCaseSidebar(caseData);

  // Update count
  document.getElementById('caseCount').textContent = Object.keys(cases).length;
  document.querySelector('.empty-state') && document.querySelector('.empty-state').remove();
}

// ── Sidebar Case Card ─────────────────────────────────────────────────────────
function addCaseSidebar(c) {
  const list = document.getElementById('caseList');
  const card = document.createElement('div');
  card.className = `case-card ${c.danger_level.toLowerCase()}`;
  card.id = `card-${c._id}`;
  card.innerHTML = `
    <div class="case-card-header">
      <span class="danger-badge ${c.danger_level.toLowerCase()}">${c.danger_level}</span>
      <span class="case-time">${timeAgo(c.created_at)}</span>
    </div>
    <h4>${c.victim_name}</h4>
    <p><i class="fas fa-phone"></i> ${c.victim_phone}</p>
    <p><i class="fas fa-tint"></i> ${c.victim_blood_group}</p>
    <p class="reason-text">${(c.danger_reasons || []).slice(0, 2).join(' • ')}</p>
    <div class="case-actions">
      <button class="btn btn-sm btn-primary" onclick="openCasePanel('${c._id}')">
        <i class="fas fa-eye"></i> View
      </button>
      <button class="btn btn-sm btn-danger" onclick="dispatchTeam('${c._id}')">
        <i class="fas fa-truck-fast"></i> Dispatch
      </button>
    </div>
  `;
  list.prepend(card);
}

// ── Case Detail Panel ─────────────────────────────────────────────────────────
function openCasePanel(caseId) {
  const c = cases[caseId];
  if (!c) return;

  const panel = document.getElementById('detailPanel');
  const body = document.getElementById('panelBody');

  body.innerHTML = `
    <div class="detail-victim">
      <div class="victim-avatar"><i class="fas fa-user"></i></div>
      <div>
        <h3>${c.victim_name}</h3>
        <p>${c.victim_phone}</p>
        <span class="blood-badge">${c.victim_blood_group}</span>
      </div>
    </div>

    <div class="danger-meter">
      <div class="meter-label">
        <span>Danger Score</span>
        <span class="danger-badge ${c.danger_level.toLowerCase()}">${c.danger_level}</span>
      </div>
      <div class="meter-bar">
        <div class="meter-fill" style="width:${c.danger_score}%; background:${DANGER_COLORS[c.danger_level]}"></div>
      </div>
      <span>${c.danger_score}/100</span>
    </div>

    <div class="reasons-list">
      <h4><i class="fas fa-brain"></i> AI Analysis</h4>
      ${(c.danger_reasons || []).map(r => `<div class="reason-item"><i class="fas fa-chevron-right"></i>${r}</div>`).join('')}
    </div>

    ${c.transcript ? `
    <div class="transcript-box">
      <h4><i class="fas fa-microphone"></i> Transcript</h4>
      <p>"${c.transcript}"</p>
    </div>` : ''}

    ${c.audio_evidence ? `
    <div class="audio-evidence">
      <h4><i class="fas fa-volume-up"></i> Audio Evidence</h4>
      <audio controls src="${c.audio_evidence}"></audio>
    </div>` : ''}

    <div class="trigger-info">
      <span class="trigger-badge">${c.trigger_type.toUpperCase()} TRIGGER</span>
      <span class="status-badge ${c.status}">${c.status.toUpperCase()}</span>
    </div>

    <div class="panel-actions">
      <button class="btn btn-danger btn-full" onclick="dispatchTeam('${c._id}')">
        <i class="fas fa-truck-fast"></i> Dispatch Backup Team
      </button>
      <button class="btn btn-success btn-full" onclick="resolveCase('${c._id}')">
        <i class="fas fa-check-circle"></i> Mark as Resolved
      </button>
    </div>
  `;

  panel.style.display = 'flex';

  // Center map on case
  map.panTo({ lat: c.location.lat, lng: c.location.lng });
  map.setZoom(14);
}

function closePanel() {
  document.getElementById('detailPanel').style.display = 'none';
}

// ── Dispatch ──────────────────────────────────────────────────────────────────
async function dispatchTeam(caseId) {
  const teams = ['Team Alpha', 'Team Bravo', 'Team Charlie', 'Team Delta'];
  const team = teams[Math.floor(Math.random() * teams.length)];

  await fetch(`/api/cases/${caseId}/dispatch`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${TOKEN()}`
    },
    body: JSON.stringify({ team })
  });

  alert(`✅ ${team} dispatched to location!`);
  document.getElementById(`card-${caseId}`).classList.add('dispatched');
}

// ── Resolve Case ──────────────────────────────────────────────────────────────
async function resolveCase(caseId) {
  await fetch(`/api/cases/${caseId}/resolve`, {
    method: 'PUT',
    headers: { 'Authorization': `Bearer ${TOKEN()}` }
  });

  // Remove from map + sidebar
  if (markers[caseId]) {
    markers[caseId].setMap(null);
    delete markers[caseId];
  }
  const card = document.getElementById(`card-${caseId}`);
  if (card) card.remove();
  delete cases[caseId];

  closePanel();
  document.getElementById('caseCount').textContent = Object.keys(cases).length;
  document.getElementById('statResolved').textContent =
    parseInt(document.getElementById('statResolved').textContent) + 1;
}

// ── Socket Listeners ──────────────────────────────────────────────────────────
function setupSocketListeners() {
  shieldSocket.on('new_case', (caseData) => {
    addCaseToMap(caseData);
    showAlertToast(caseData);
    playAlertSound();
    updateStats(Object.values(cases));
  });

  shieldSocket.on('location_update', ({ case_id, lat, lng }) => {
    if (markers[case_id]) {
      markers[case_id].setPosition({ lat, lng });
    }
    if (cases[case_id]) {
      cases[case_id].location.lat = lat;
      cases[case_id].location.lng = lng;
    }
  });

  shieldSocket.on('case_resolved', ({ case_id }) => {
    if (markers[case_id]) {
      markers[case_id].setMap(null);
    }
    const card = document.getElementById(`card-${case_id}`);
    if (card) card.remove();
    delete cases[case_id];
  });
}

// ── Alert Toast ───────────────────────────────────────────────────────────────
function showAlertToast(c) {
  document.getElementById('toastTitle').textContent = `🚨 NEW ${c.danger_level} ALERT`;
  document.getElementById('toastDesc').textContent =
    `${c.victim_name} — ${(c.danger_reasons || ['Panic triggered'])[0]}`;
  const toast = document.getElementById('alertToast');
  toast.style.display = 'flex';
  setTimeout(closeToast, 8000);
}

function closeToast() {
  document.getElementById('alertToast').style.display = 'none';
}

function playAlertSound() {
  const audio = document.getElementById('alertSound');
  if (audio) audio.play().catch(() => {});
}

// ── Stats Update ──────────────────────────────────────────────────────────────
function updateStats(caseList) {
  document.getElementById('statCritical').textContent =
    caseList.filter(c => c.danger_level === 'CRITICAL').length;
  document.getElementById('statHigh').textContent =
    caseList.filter(c => c.danger_level === 'HIGH').length;
  document.getElementById('statDispatched').textContent =
    caseList.filter(c => c.status === 'dispatched').length;
}

function filterCases(level) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');

  document.querySelectorAll('.case-card').forEach(card => {
    card.style.display = (level === 'all' || card.classList.contains(level.toLowerCase()))
      ? 'block' : 'none';
  });
}

function timeAgo(dateStr) {
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 60000);
  if (diff < 1) return 'Just now';
  if (diff < 60) return `${diff}m ago`;
  return `${Math.floor(diff/60)}h ago`;
}
