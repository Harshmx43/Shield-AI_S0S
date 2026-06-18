from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import create_user, find_user_by_phone, verify_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('phone') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Name, phone and password are required'}), 400

    existing = find_user_by_phone(data['phone'])
    if existing:
        return jsonify({'error': 'Phone already registered'}), 409

    # Validate trusted contacts
    contacts = data.get('trusted_contacts', [])
    if len(contacts) < 1:
        return jsonify({'error': 'At least 1 trusted contact required'}), 400

    user_id = create_user(data)
    token = create_access_token(identity=user_id)

    return jsonify({
        'message': 'Registered successfully',
        'token': token,
        'user_id': user_id,
        'role': data.get('role', 'user')
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    user = find_user_by_phone(data.get('phone'))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not verify_password(data.get('password', ''), user['password']):
        return jsonify({'error': 'Invalid password'}), 401

    token = create_access_token(identity=str(user['_id']))

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user_id': str(user['_id']),
        'name': user['name'],
        'role': user.get('role', 'user'),
        'mic_consent': user.get('mic_consent', False)
    }), 200
