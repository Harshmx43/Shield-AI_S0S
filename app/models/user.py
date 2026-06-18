from datetime import datetime
from app import get_db
import bcrypt

def create_user(data):
    db = get_db()
    hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt())
    user = {
        'name': data['name'],
        'phone': data['phone'],
        'password': hashed,
        'age': data.get('age'),
        'blood_group': data.get('blood_group'),
        'photo': data.get('photo', ''),
        'trusted_contacts': data.get('trusted_contacts', []),
        'mic_consent': data.get('mic_consent', False),
        'consent_timestamp': datetime.utcnow(),
        'wearable_linked': False,
        'role': data.get('role', 'user'),  # user | authority
        'created_at': datetime.utcnow()
    }
    result = db.users.insert_one(user)
    return str(result.inserted_id)

def find_user_by_phone(phone):
    db = get_db()
    return db.users.find_one({'phone': phone})

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode(), hashed)

def get_user_by_id(user_id):
    from bson import ObjectId
    db = get_db()
    return db.users.find_one({'_id': ObjectId(user_id)})
