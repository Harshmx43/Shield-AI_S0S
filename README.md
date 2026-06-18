# 🛡️ ShieldAI — Intelligent Distress Detection & Rapid Response System

## 👥 Role-Based Access

| Role | Access | Redirect After Login |
|------|--------|----------------------|
| 👤 **User** | Panic button, witness report, wearable simulation | `/user/home` |
| 🚔 **Authority** | Live map dashboard, dispatch cases, resolve alerts | `/dashboard/` |
| 👑 **Admin** | Full system: manage users, view all cases, system stats | `/admin/` |

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone <repo>
cd shieldai
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 3. Download AI models
```bash
python -c "import whisper; whisper.load_model('base')"
```

### 4. Run
```bash
python run.py
```

Visit: `http://localhost:5000`

---

## 🔑 Environment Variables (.env)

```
MONGO_URI=mongodb+srv://...        # MongoDB Atlas connection string
JWT_SECRET_KEY=your_secret         # Any random secret string
TWILIO_ACCOUNT_SID=...             # Twilio for SMS alerts
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE=+1234567890
CLOUDINARY_CLOUD_NAME=...          # Cloudinary for audio storage
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
GOOGLE_MAPS_API_KEY=...            # Google Maps for dashboard
```

---

## 📁 Project Structure

```
shieldai/
├── run.py                          # Entry point
├── requirements.txt
├── .env.example
└── app/
    ├── __init__.py                 # Flask factory
    ├── middleware/
    │   └── roles.py               # Role-based access control
    ├── models/
    │   ├── user.py                 # User DB operations
    │   ├── case.py                 # Case DB operations
    │   └── witness.py             # Witness DB operations
    ├── routes/
    │   ├── auth.py                 # Login / Register
    │   ├── admin.py               # Admin APIs
    │   ├── cases.py               # Case trigger/dispatch
    │   ├── dashboard.py           # Authority dashboard
    │   ├── location.py            # Live GPS updates
    │   ├── user.py                # User pages
    │   └── witness.py             # Witness reports
    ├── ai/
    │   ├── transcribe.py          # Whisper STT
    │   ├── distress_nlp.py        # NLP keyword detection
    │   └── danger_score.py        # AI scoring engine
    ├── sockets/
    │   └── events.py              # Real-time SocketIO
    ├── static/
    │   ├── css/
    │   │   ├── style.css          # Main dark theme
    │   │   └── admin.css          # Admin panel styles
    │   └── js/
    │       ├── panic.js           # Panic button logic
    │       ├── map.js             # Authority live map
    │       ├── socket.js          # SocketIO client
    │       └── wearable.js        # Wearable simulation
    └── templates/
        ├── base.html
        ├── auth/
        │   ├── login.html
        │   └── register.html
        ├── user/
        │   ├── home.html          # Panic button page
        │   ├── wearable.html      # Wearable simulator
        │   └── witness.html       # Witness report
        ├── dashboard/
        │   └── index.html         # Authority map dashboard
        └── admin/
            └── index.html         # Admin control panel
```

---

## 👨‍💻 Team Division

### Person 1 — Frontend
`style.css`, `admin.css`, all HTML templates

### Person 2 — Backend
`__init__.py`, all routes/, all models/, `sockets/events.py`

### Person 3 — AI/ML
`ai/transcribe.py`, `ai/distress_nlp.py`, `ai/danger_score.py`, `js/panic.js`, `js/map.js`, `js/wearable.js`

---

## 🎯 Demo Flow (3 minutes)

1. **Register** as User → gets redirected to panic button page
2. **Trigger SOS** (shake / 3 clicks) → alert fires
3. **Authority dashboard** shows live red pin on map
4. **Dispatch** backup team → case status updates
5. **Admin panel** shows full system stats + user management

---

## 🔮 Future Scope (Mobile)
- React Native app with background location
- BLE wearable band (ESP32 + MAX30102)
- Always-on distress monitoring
- Offline-first mode for rural areas
