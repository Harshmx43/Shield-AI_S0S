from datetime import datetime
from app import get_db
from bson import ObjectId

def create_case(data):
    db = get_db()
    case = {
        'victim_id': data['victim_id'],
        'victim_name': data['victim_name'],
        'victim_phone': data['victim_phone'],
        'victim_blood_group': data.get('victim_blood_group', 'Unknown'),
        'trigger_type': data.get('trigger_type', 'panic'),
        'danger_score': 0,
        'danger_level': 'ANALYZING',
        'danger_reasons': [],
        'location': {
            'lat': data['lat'],
            'lng': data['lng'],
            'address': data.get('address', ''),
            'history': [{'lat': data['lat'], 'lng': data['lng'], 'timestamp': datetime.utcnow()}]
        },
        'audio_evidence': data.get('audio_url', ''),
        'transcript': '',
        'keywords_found': [],
        'biometrics': {
            'heart_rate': data.get('heart_rate', 0),
            'fall_detected': data.get('fall_detected', False),
            'struggle_detected': data.get('struggle_detected', False)
        },
        'status': 'active',
        'assigned_team': '',
        'created_at': datetime.utcnow(),
        'resolved_at': None
    }
    result = db.cases.insert_one(case)
    case_id = str(result.inserted_id)
    # ── Write system log ──────────────────────────────────────────────────────
    write_log('case_created', f"New {data.get('trigger_type','panic')} case created for {data['victim_name']}", case_id)
    return case_id

def get_active_cases():
    db = get_db()
    # Only return active/dispatched — NOT resolved
    cases = list(db.cases.find({'status': {'$in': ['active', 'dispatched']}}))
    for c in cases:
        c['_id'] = str(c['_id'])
    return cases

def get_case_by_id(case_id):
    db = get_db()
    try:
        case = db.cases.find_one({'_id': ObjectId(case_id)})
        if case:
            case['_id'] = str(case['_id'])
        return case
    except Exception:
        return None

def update_case(case_id, updates):
    db = get_db()
    try:
        db.cases.update_one({'_id': ObjectId(case_id)}, {'$set': updates})
    except Exception as e:
        print(f"update_case error: {e}")

def update_location(case_id, lat, lng):
    db = get_db()
    try:
        db.cases.update_one(
            {'_id': ObjectId(case_id)},
            {
                '$set': {'location.lat': lat, 'location.lng': lng},
                '$push': {'location.history': {'lat': lat, 'lng': lng, 'timestamp': datetime.utcnow()}}
            }
        )
    except Exception as e:
        print(f"update_location error: {e}")

def resolve_case(case_id):
    db = get_db()
    try:
        # Get case info for log
        case = db.cases.find_one({'_id': ObjectId(case_id)})
        result = db.cases.update_one(
            {'_id': ObjectId(case_id)},
            {'$set': {'status': 'resolved', 'resolved_at': datetime.utcnow()}}
        )
        print(f"✅ Resolved case {case_id} — matched: {result.matched_count}, modified: {result.modified_count}")
        # ── Write system log ──────────────────────────────────────────────────
        name = case.get('victim_name', 'Unknown') if case else 'Unknown'
        write_log('case_resolved', f"Case resolved for {name}", case_id)
    except Exception as e:
        print(f"❌ resolve_case error: {e}")

def dispatch_case(case_id, team_name):
    db = get_db()
    try:
        case = db.cases.find_one({'_id': ObjectId(case_id)})
        db.cases.update_one(
            {'_id': ObjectId(case_id)},
            {'$set': {'status': 'dispatched', 'assigned_team': team_name}}
        )
        # ── Write system log ──────────────────────────────────────────────────
        name = case.get('victim_name', 'Unknown') if case else 'Unknown'
        write_log('dispatch', f"{team_name} dispatched to {name}", case_id)
    except Exception as e:
        print(f"❌ dispatch_case error: {e}")

def write_log(action, message, case_id=None):
    """Write a system log entry to MongoDB"""
    try:
        db = get_db()
        db.logs.insert_one({
            'action': action,
            'message': message,
            'case_id': case_id,
            'timestamp': datetime.utcnow()
        })
    except Exception as e:
        print(f"write_log error: {e}")
