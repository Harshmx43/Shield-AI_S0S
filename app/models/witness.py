from datetime import datetime
from app import get_db
from bson import ObjectId

def create_witness_report(data):
    db = get_db()
    report = {
        'witness_id': data.get('witness_id', 'anonymous'),
        'location': {
            'lat': data['lat'],
            'lng': data['lng']
        },
        'voice_note': data.get('voice_note', ''),
        'description': data.get('description', ''),
        'linked_case_id': data.get('linked_case_id', None),
        'timestamp': datetime.utcnow()
    }
    result = db.witness_reports.insert_one(report)
    return str(result.inserted_id)

def get_nearby_witnesses(lat, lng, radius_km=1):
    db = get_db()
    # Simple bounding box search for hackathon
    delta = radius_km / 111
    reports = list(db.witness_reports.find({
        'location.lat': {'$gte': lat - delta, '$lte': lat + delta},
        'location.lng': {'$gte': lng - delta, '$lte': lng + delta}
    }))
    for r in reports:
        r['_id'] = str(r['_id'])
    return reports
