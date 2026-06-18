from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.case import (create_case, get_active_cases, get_case_by_id,
                              update_case, resolve_case, dispatch_case)
from app.models.user import get_user_by_id
from app import socketio
import cloudinary
import cloudinary.uploader
import os, base64, tempfile

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

cases_bp = Blueprint('cases', __name__)

@cases_bp.route('/trigger', methods=['POST'])
@jwt_required()
def trigger_case():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    # Upload audio to Cloudinary if present
    audio_url = ''
    if data.get('audio_base64'):
        try:
            audio_data = base64.b64decode(data['audio_base64'])
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
                f.write(audio_data)
                tmp_path = f.name
            result = cloudinary.uploader.upload(
                tmp_path,
                resource_type='video',
                folder='shieldai/evidence'
            )
            audio_url = result['secure_url']
            os.unlink(tmp_path)
        except Exception as e:
            print(f"Audio upload error: {e}")

    # Create case
    case_id = create_case({
        'victim_id': user_id,
        'victim_name': user['name'],
        'victim_phone': user['phone'],
        'victim_blood_group': user.get('blood_group', 'Unknown'),
        'trigger_type': data.get('trigger_type', 'panic'),
        'lat': data['lat'],
        'lng': data['lng'],
        'address': data.get('address', ''),
        'audio_url': audio_url,
        'heart_rate': data.get('heart_rate', 0),
        'fall_detected': data.get('fall_detected', False),
        'struggle_detected': data.get('struggle_detected', False)
    })

    # Run AI analysis async (fire and forget for hackathon)
    try:
        from app.ai.danger_score import analyze_case
        ai_result = analyze_case({
            'audio_url': audio_url,
            'heart_rate': data.get('heart_rate', 0),
            'fall_detected': data.get('fall_detected', False),
            'struggle_detected': data.get('struggle_detected', False),
            'transcript': data.get('transcript', '')
        })
        update_case(case_id, {
            'danger_score': ai_result['score'],
            'danger_level': ai_result['level'],
            'danger_reasons': ai_result['reasons'],
            'keywords_found': ai_result.get('keywords', []),
            'transcript': ai_result.get('transcript', '')
        })
    except Exception as e:
        print(f"AI analysis error: {e}")
        update_case(case_id, {'danger_score': 75, 'danger_level': 'HIGH', 'danger_reasons': ['Manual trigger activated']})

    # Emit to authority dashboard via SocketIO
    case_data = get_case_by_id(case_id)
    socketio.emit('new_case', case_data)

    # Store vectors for semantic search
    try:
        from app.ai.vector_search import store_case_vectors
        case_data = get_case_by_id(case_id)
        store_case_vectors(
            case_id=case_id,
            transcript=case_data.get('transcript', ''),
            danger_reasons=case_data.get('danger_reasons', []),
            danger_level=case_data.get('danger_level', ''),
            trigger_type=data.get('trigger_type', 'panic')
        )
    except Exception as e:
        print(f"Vector storage error: {e}")

    # Send SMS to trusted contacts
    try:
        from app.ai.distress_nlp import send_sms_alerts
        send_sms_alerts(user.get('trusted_contacts', []), user['name'], data['lat'], data['lng'], case_id)
    except Exception as e:
        print(f"SMS error: {e}")

    return jsonify({'message': 'Alert triggered', 'case_id': case_id}), 201


@cases_bp.route('/active', methods=['GET'])
@jwt_required()
def active_cases():
    cases = get_active_cases()
    return jsonify(cases), 200


@cases_bp.route('/<case_id>', methods=['GET'])
@jwt_required()
def get_case(case_id):
    case = get_case_by_id(case_id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    return jsonify(case), 200


@cases_bp.route('/<case_id>/resolve', methods=['PUT'])
def resolve(case_id):
    resolve_case(case_id)
    socketio.emit('case_resolved', {'case_id': case_id})
    return jsonify({'message': 'Case resolved'}), 200


@cases_bp.route('/<case_id>/dispatch', methods=['PUT'])
def dispatch(case_id):
    data = request.get_json()
    team = data.get('team', 'Team Alpha')
    dispatch_case(case_id, team)
    socketio.emit('case_dispatched', {'case_id': case_id, 'team': team})
    return jsonify({'message': f'Team {team} dispatched'}), 200
