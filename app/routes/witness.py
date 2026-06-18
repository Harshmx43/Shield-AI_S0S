from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.witness import create_witness_report, get_nearby_witnesses
from app.models.case import get_active_cases
from app import socketio
import math

witness_bp = Blueprint('witness', __name__)

def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@witness_bp.route('/report', methods=['POST'])
@jwt_required()
def report():
    user_id = get_jwt_identity()
    data = request.get_json()

    lat = data.get('lat')
    lng = data.get('lng')

    # Check if any active case is nearby (within 500m)
    active_cases = get_active_cases()
    linked_case_id = None
    for case in active_cases:
        case_lat = case['location']['lat']
        case_lng = case['location']['lng']
        dist = haversine(lat, lng, case_lat, case_lng)
        if dist <= 0.5:  # 500 meters
            linked_case_id = case['_id']
            break

    report_id = create_witness_report({
        'witness_id': user_id,
        'lat': lat,
        'lng': lng,
        'description': data.get('description', ''),
        'voice_note': data.get('voice_note', ''),
        'linked_case_id': linked_case_id
    })

    # Emit to dashboard
    socketio.emit('witness_report', {
        'report_id': report_id,
        'lat': lat,
        'lng': lng,
        'linked_case_id': linked_case_id,
        'description': data.get('description', '')
    })

    return jsonify({
        'message': 'Report submitted',
        'report_id': report_id,
        'linked_case': linked_case_id
    }), 201
