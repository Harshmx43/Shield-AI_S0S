import re
import os
from twilio.rest import Client

# ─── Distress Keywords (multilingual) ───────────────────────────────────────
DISTRESS_KEYWORDS = {
    'english': [
        'help', 'help me', 'save me', 'stop', 'leave me', 'let me go',
        'dont touch', "don't touch", 'get off', 'please stop', 'no no',
        'someone help', 'call police', 'im scared', "i'm scared",
        'he is hitting', 'she is hitting', 'attacking me', 'robbery',
        'fire', 'danger', 'emergency', 'assault', 'kidnap'
    ],
    'hindi': [
        'bachao', 'madad', 'chodo', 'mat karo', 'chhod do', 'help karo',
        'police bulao', 'mujhe chodo', 'mujhe maaro mat', 'bachao mujhe',
        'koi hai', 'meri madad karo', 'khatra', 'aag', 'chor'
    ],
    'punjabi': [
        'chaddo', 'madad karo', 'bachao', 'police sad', 'khatra',
        'naa karo', 'jaane do', 'help karo'
    ]
}

# Flatten all keywords into one list
ALL_KEYWORDS = []
for lang_keywords in DISTRESS_KEYWORDS.values():
    ALL_KEYWORDS.extend(lang_keywords)

# ─── Screaming / Panic Indicators ────────────────────────────────────────────
PANIC_PATTERNS = [
    r'\b(aaa+h*|eee+k*|ooo+h*)\b',  # screaming sounds
    r'\bno+\b',                       # repeated no
    r'\bhelp\s+help\b',               # repeated help
    r'[!]{2,}',                       # multiple exclamation marks
]

def detect_keywords(transcript):
    """Detect distress keywords in transcript"""
    if not transcript:
        return [], 0

    transcript_lower = transcript.lower()
    found = []

    for keyword in ALL_KEYWORDS:
        if keyword in transcript_lower:
            found.append(keyword)

    # Remove duplicates
    found = list(set(found))
    return found, len(found)

def detect_panic_patterns(transcript):
    """Detect panic speech patterns"""
    if not transcript:
        return False

    for pattern in PANIC_PATTERNS:
        if re.search(pattern, transcript, re.IGNORECASE):
            return True
    return False

def analyze_transcript(transcript):
    """Full NLP analysis of transcript"""
    keywords_found, keyword_count = detect_keywords(transcript)
    has_panic = detect_panic_patterns(transcript)

    return {
        'keywords_found': keywords_found,
        'keyword_count': keyword_count,
        'has_panic_patterns': has_panic,
        'keyword_score': min(keyword_count * 15, 45),  # max 45 points
        'panic_score': 20 if has_panic else 0
    }

def send_sms_alerts(trusted_contacts, victim_name, lat, lng, case_id):
    """Send SMS to all trusted contacts via Twilio"""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_phone = os.getenv('TWILIO_PHONE')

    if not account_sid or not auth_token:
        print("Twilio not configured, skipping SMS")
        return

    client = Client(account_sid, auth_token)
    maps_link = f"https://maps.google.com/?q={lat},{lng}"

    message = (
        f"🚨 SHIELDAI EMERGENCY ALERT 🚨\n"
        f"{victim_name} has triggered a distress alert!\n"
        f"📍 Location: {maps_link}\n"
        f"Case ID: {case_id}\n"
        f"Please respond immediately or call emergency services."
    )

    for contact in trusted_contacts:
        try:
            client.messages.create(
                body=message,
                from_=from_phone,
                to=contact.get('phone', '')
            )
            print(f"SMS sent to {contact.get('name')}")
        except Exception as e:
            print(f"SMS failed for {contact.get('name')}: {e}")
