from flask import Blueprint, render_template
from app.models.case import get_active_cases, get_case_by_id
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import json

dashboard_bp = Blueprint('dashboard', __name__)

IST = timezone(timedelta(hours=5, minutes=30))

def serialize_case(case):
    c = dict(case)
    c['_id'] = str(c['_id'])
    # Convert all datetime → IST ✅
    for key, val in list(c.items()):
        if isinstance(val, datetime):
            ist = val.replace(tzinfo=timezone.utc).astimezone(IST)
            c[key] = ist.isoformat()
    # Fix nested location history datetimes
    if 'location' in c and isinstance(c['location'], dict):
        for h in c['location'].get('history', []):
            if isinstance(h.get('timestamp'), datetime):
                ist = h['timestamp'].replace(tzinfo=timezone.utc).astimezone(IST)
                h['timestamp'] = ist.isoformat()
    if 'victim_id' in c:
        c['victim_id'] = str(c['victim_id'])
    c.pop('transcript_vector', None)
    c.pop('description_vector', None)
    c.pop('danger_pattern_vector', None)
    return c

@dashboard_bp.route('/', methods=['GET'])
def index():
    try:
        raw_cases = get_active_cases()
        cases = [serialize_case(c) for c in raw_cases]
        cases_json = json.dumps(cases)
    except Exception as e:
        print(f"Dashboard error: {e}")
        cases_json = '[]'
    return render_template('dashboard/index.html', cases_json=cases_json)

@dashboard_bp.route('/case/<case_id>', methods=['GET'])
def case_detail(case_id):
    case = get_case_by_id(case_id)
    return render_template('dashboard/case.html', case=case)