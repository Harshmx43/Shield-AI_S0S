from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/home')
def home():
    return render_template('user/home.html')

@user_bp.route('/wearable')
def wearable():
    return render_template('user/wearable.html')

@user_bp.route('/witness')
def witness():
    maps_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    return render_template('user/witness.html', maps_key=maps_key)
