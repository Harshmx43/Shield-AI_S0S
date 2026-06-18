from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required
from app.middleware.roles import admin_required, get_current_user
from app import get_db
from bson import ObjectId
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# ── Admin Dashboard Page ──────────────────────────────────────────────────────
@admin_bp.route('/')
def index():
    return render_template('admin/index.html')

# ── System Stats ──────────────────────────────────────────────────────────────
@admin_bp.route('/api/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_stats():
    db = get_db()
    stats = {
        'total_users':       db.users.count_documents({}),
        'total_authorities': db.users.count_documents({'role': 'authority'}),
        'total_admins':      db.users.count_documents({'role': 'admin'}),
        'active_cases':      db.cases.count_documents({'status': {'$in': ['active', 'dispatched']}}),
        'resolved_today':    db.cases.count_documents({
            'status': 'resolved',
            'resolved_at': {'$gte': datetime.utcnow().replace(hour=0, minute=0, second=0)}
        }),
        'total_cases':       db.cases.count_documents({}),
        'critical_cases':    db.cases.count_documents({'danger_level': 'CRITICAL', 'status': 'active'}),
        'false_alarms':      db.cases.count_documents({'status': 'false_alarm'}),
        'total_witnesses':   db.witness_reports.count_documents({}),
    }
    return jsonify(stats), 200

# ── User Management ───────────────────────────────────────────────────────────
@admin_bp.route('/api/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    db = get_db()
    role_filter = request.args.get('role')
    query = {'role': role_filter} if role_filter else {}
    users = list(db.users.find(query, {'password': 0}))  # exclude password
    for u in users:
        u['_id'] = str(u['_id'])
        if 'created_at' in u:
            u['created_at'] = u['created_at'].isoformat()
    return jsonify(users), 200

@admin_bp.route('/api/users/<user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user(user_id):
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user['_id'] = str(user['_id'])
    return jsonify(user), 200

@admin_bp.route('/api/users/<user_id>/role', methods=['PUT'])
@jwt_required()
@admin_required
def update_role(user_id):
    data = request.get_json()
    new_role = data.get('role')
    if new_role not in ['user', 'authority', 'admin']:
        return jsonify({'error': 'Invalid role'}), 400
    db = get_db()
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'role': new_role}})
    return jsonify({'message': f'Role updated to {new_role}'}), 200

@admin_bp.route('/api/users/<user_id>/suspend', methods=['PUT'])
@jwt_required()
@admin_required
def suspend_user(user_id):
    db = get_db()
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'suspended': True}})
    return jsonify({'message': 'User suspended'}), 200

@admin_bp.route('/api/users/<user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    db = get_db()
    db.users.delete_one({'_id': ObjectId(user_id)})
    return jsonify({'message': 'User deleted'}), 200

# ── All Cases (Admin View) ────────────────────────────────────────────────────
@admin_bp.route('/api/cases', methods=['GET'])
@jwt_required()
@admin_required
def get_all_cases():
    db = get_db()
    status = request.args.get('status')
    query = {'status': status} if status else {}
    cases = list(db.cases.find(query).sort('created_at', -1).limit(100))
    for c in cases:
        c['_id'] = str(c['_id'])
        if 'created_at' in c:
            c['created_at'] = c['created_at'].isoformat()
        if c.get('resolved_at'):
            c['resolved_at'] = c['resolved_at'].isoformat()
    return jsonify(cases), 200

@admin_bp.route('/api/cases/<case_id>/flag', methods=['PUT'])
@jwt_required()
@admin_required
def flag_false_alarm(case_id):
    db = get_db()
    db.cases.update_one({'_id': ObjectId(case_id)}, {'$set': {'status': 'false_alarm'}})
    return jsonify({'message': 'Case flagged as false alarm'}), 200

# ── System Logs ───────────────────────────────────────────────────────────────
@admin_bp.route('/api/logs', methods=['GET'])
@jwt_required()
@admin_required
def get_logs():
    db = get_db()
    logs = list(db.logs.find().sort('timestamp', -1).limit(50))
    for l in logs:
        l['_id'] = str(l['_id'])
        if 'timestamp' in l:
            l['timestamp'] = l['timestamp'].isoformat()
    return jsonify(logs), 200
