from flask import Flask
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Force load .env from same folder as this file
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '..', '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
jwt = JWTManager()
db = None

def create_app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'shieldai-secret')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    CORS(app)
    socketio.init_app(app)
    jwt.init_app(app)

    global db
    MONGO_URI = os.getenv('MONGO_URI')
    print("🔍 MONGO_URI =", MONGO_URI)  # ← This will show in terminal

    if not MONGO_URI:
        raise ValueError("❌ MONGO_URI not found! Check your .env file location.")

    client = MongoClient(MONGO_URI)
    db = client['shieldai']
    print("✅ Connected to MongoDB Atlas!")

    from app.routes.auth import auth_bp
    from app.routes.cases import cases_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.witness import witness_bp
    from app.routes.location import location_bp
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cases_bp, url_prefix='/api/cases')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(witness_bp, url_prefix='/api/witness')
    app.register_blueprint(location_bp, url_prefix='/api/location')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.sockets.events import register_events
    register_events(socketio)

    return app

def get_db():
    return db