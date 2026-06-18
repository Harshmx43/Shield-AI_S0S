from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.case import update_location, get_case_by_id
from app import socketio

location_bp = Blueprint('location', __name__)

@location_bp.route('/update', methods=['POST'])
@jwt_required()
def update():
    data = request.get_json()
    case_id = data.get('case_id')
    lat = data.get('lat')
    lng = data.get('lng')

    if not case_id or not lat or not lng:
        return jsonify({'error': 'case_id, lat, lng required'}), 400

    update_location(case_id, lat, lng)

    # Emit live location update to dashboard
    socketio.emit('location_update', {
        'case_id': case_id,
        'lat': lat,
        'lng': lng
    })

    return jsonify({'message': 'Location updated'}), 200

@location_bp.route('/<case_id>', methods=['GET'])
@jwt_required()
def get_location_history(case_id):
    case = get_case_by_id(case_id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    return jsonify(case.get('location', {})), 200
