from flask import Flask, request, jsonify
from flask_dance.contrib.google import make_google_blueprint
from flask_cors import CORS
from flask_migrate import Migrate
import os
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from models import Users, Contacts, db, ActivityLog
from dotenv import load_dotenv
import uuid
import datetime
app = Flask(__name__)
# CORS(app)
# Replace the simple CORS(app) with this:
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000", "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], "allow_headers": "*"}})
load_dotenv()  

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

db.init_app(app)
migrate = Migrate(app, db)

jwt = JWTManager(app)

# Google OAuth Configuration
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_to="google_auth"
)
app.register_blueprint(google_bp, url_prefix="/login")


@app.route("/")
def home():
    return "Flask is running successfully!"

@app.route('/login/google', methods=['POST'])
def google_auth():
    data = request.json
    if not data or not data.get('email') or not data.get('oauth_id'):
        return jsonify({"error": "Invalid request data"}), 400

    email = data["email"]
    name = data.get("name", "")
    oauth_id = data["oauth_id"]
    oauth_provider = data.get("oauth_provider", "google")

    user = Users.query.filter_by(oauth_provider=oauth_provider, oauth_id=oauth_id).first()
    if not user:
        user = Users(name=name, email=email, oauth_provider=oauth_provider, oauth_id=oauth_id)
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": user.to_dict()
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Name, email, and password are required'}), 400

    if Users.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already in use'}), 400

    new_user = Users(name=data['name'], email=data['email'])
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# Logout
@app.route("/logout")
@jwt_required()
def logout():
    return jsonify({"message": "Token revoked (implement token blacklist)"}), 200


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    user = Users.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token, 'user': user.to_dict()}), 200

@app.route('/api/contacts', methods=['POST'])
@jwt_required()
def create_contact():
    user_id = get_jwt_identity()
    data = request.json
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({'error': 'Name and email are required'}), 400

    new_contact = Contacts(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone', ''),
        categories=data.get('categories', []),
        status=data.get('status', 'active'),
        favorite=data.get('favorite', False),
        user_id=user_id
    )

    db.session.add(new_contact)
    
    activity_log = ActivityLog(
        user_id = user_id,
        timestamp=datetime.datetime.now(),
        action='added',
        action_type='',
        contact_name= data['name']
    )
    db.session.add(activity_log)
    db.session.commit()

    return jsonify(new_contact.to_dict()), 201

@app.route('/api/contacts', methods=['GET'])
@jwt_required()
def get_contacts():
    user_id = get_jwt_identity()
    contacts = Contacts.query.filter_by(user_id=user_id).all()
    return jsonify([contact.to_dict() for contact in contacts])


@app.route('/api/contacts/<string:id>', methods=['GET'])
@jwt_required()
def get_contact(id):
    id = uuid.UUID(id)
    user_id = get_jwt_identity()
    contact = Contacts.query.filter_by(id=id, user_id=user_id).first()
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    return jsonify(contact.to_dict())

@app.route('/api/user-activities', methods=['GET'])
@jwt_required()
def get_user_activities():
    user_id = get_jwt_identity()
    user_activities = ActivityLog.query.filter_by(user_id=user_id).all()
    return jsonify([user_activity.to_dict() for user_activity in user_activities])

@app.route('/api/contacts/<string:id>', methods=['PUT'])
@jwt_required()
def update_contact(id):
    id = uuid.UUID(id)
    user_id = get_jwt_identity()
    contact = Contacts.query.filter_by(id=id, user_id=user_id).first()

    if not contact:
        return jsonify({'error': 'Contact not found'}), 404

    data = request.json
    contact.name = data.get('name', contact.name)
    contact.email = data.get('email', contact.email)
    contact.phone = data.get('phone', contact.phone)
    contact.categories = data.get('categories', contact.categories)
    contact.status = data.get('status', contact.status)  
    contact.favorite = data.get('favorite', contact.favorite)

    db.session.commit()
    activity = ActivityLog(\
        user_id = user_id,
        timestamp=datetime.datetime.now(),
        action='updated',
        action_type='',
        contact_name= contact.name
    )
    db.session.add(activity)
    return jsonify(contact.to_dict())

@app.route('/api/contacts/<string:id>/toggle-favorite', methods=['PATCH'])
@jwt_required()
def toggle_favorite(id):
    id = uuid.UUID(id)
    user_id = get_jwt_identity()
    contact = Contacts.query.filter_by(id=id, user_id=user_id).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    contact.favorite = not contact.favorite
    activity = ActivityLog(
        user_id=user_id,
        timestamp=datetime.datetime.now(),
        action='toggle_favorite',
        contact_name= contact.name,
        action_type="not favorite" if contact.favorite else "favorite"
    )
    db.session.add(activity)
    
    db.session.commit()
    
    return jsonify({'message': 'Favorite status updated', 'favorite': contact.favorite})

@app.route('/api/contacts/<string:id>/set-status', methods=['PATCH'])
@jwt_required()
def set_status(id):
    id = uuid.UUID(id)
    user_id = get_jwt_identity()
    contact = Contacts.query.filter_by(id=id, user_id=user_id).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    data = request.json
    if not data or not data.get('status'):
        return jsonify({'error': 'Status is required'}), 400
    
    # Validate status
    valid_statuses = ['active', 'blocked', 'bin']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Status must be one of: {", ".join(valid_statuses)}'}), 400
    
    contact.status = data['status']
    activity = ActivityLog(
        user_id=user_id,
        timestamp=datetime.datetime.now(),
        action='set_status',
        contact_name= contact.name,
        action_type=data['status']
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'message': 'Status updated', 'status': contact.status})

@app.route('/api/contacts/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_contact(id):
    id = uuid.UUID(id)
    user_id = get_jwt_identity()
    contact = Contacts.query.filter_by(id=id, user_id=user_id).first()

    if not contact:
        return jsonify({'error': 'Contact not found'}), 404

    activity = ActivityLog(
        user_id=user_id,
        action='deleted',
        action_type='',
        timestamp=datetime.datetime.now(),
        contact_name= contact.name
    )
    db.session.add(activity)
    db.session.delete(contact)
    db.session.commit()

    return jsonify({'message': 'Contact deleted successfully'}), 200


if __name__ == '__main__':
    app.run(debug=True)
