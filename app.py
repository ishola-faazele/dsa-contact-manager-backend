from flask import Flask, request, jsonify, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_cors import CORS
from flask_migrate import Migrate
import os
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from models import Users, Contacts, db
from flask_login import LoginManager, login_user, logout_user
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
load_dotenv()  

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_secure_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "contactshub")

app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "supersecretkey")

db.init_app(app)
migrate = Migrate(app, db)

jwt = JWTManager(app)

login_manager = LoginManager()
login_manager.init_app(app)

# Google OAuth Configuration
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_to="google_auth"
)
app.register_blueprint(google_bp, url_prefix="/login")

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/login/google')
def google_auth():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if resp.ok:
        user_info = resp.json()
        email = user_info["email"]
        name = user_info.get("name", "")
        oauth_id = user_info.get("id")
        oauth_provider = "google"

        user = Users.query.filter_by(oauth_provider=oauth_provider, oauth_id=oauth_id).first()
        if not user:
            user = Users(name=name, email=email, oauth_provider=oauth_provider, oauth_id=oauth_id)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        access_token = create_access_token(identity=user.id)
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": user.to_dict()
        })

    return jsonify({"error": "Google authentication failed"}), 400

# Logout
@app.route("/logout")
@jwt_required()
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})


@app.route("/")
def home():
    return "Flask is running successfully!"


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


@app.route('/api/contacts', methods=['GET'])
@jwt_required()
def get_contacts():
    user_id = get_jwt_identity()
    contacts = Contacts.query.filter_by(user_id=user_id).all()
    return jsonify([contact.to_dict() for contact in contacts])


@app.route('/api/contacts/<int:id>', methods=['GET'])
@jwt_required()
def get_contact(id):
    user_id = get_jwt_identity()
    contact = Contacts.query.filter_by(id=id, user_id=user_id).first()
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    return jsonify(contact.to_dict())


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
        user_id=user_id
    )

    db.session.add(new_contact)
    db.session.commit()

    return jsonify(new_contact.to_dict()), 201


@app.route('/api/contacts/<int:id>', methods=['PUT'])
@jwt_required()
def update_contact(id):
    user_id = get_jwt_identity()
    contact = Contacts.query.filter_by(id=id, user_id=user_id).first()

    if not contact:
        return jsonify({'error': 'Contact not found'}), 404

    data = request.json
    contact.name = data.get('name', contact.name)
    contact.email = data.get('email', contact.email)
    contact.phone = data.get('phone', contact.phone)
    contact.categories = data.get('categories', contact.categories)

    db.session.commit()
    return jsonify(contact.to_dict())


@app.route('/api/contacts/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_contact(id):
    user_id = get_jwt_identity()
    contact = Contacts.query.filter_by(id=id, user_id=user_id).first()

    if not contact:
        return jsonify({'error': 'Contact not found'}), 404

    db.session.delete(contact)
    db.session.commit()

    return jsonify({'message': 'Contact deleted successfully'}), 200


@app.route('/api/contacts/search', methods=['GET'])
@jwt_required()
def search_and_sort_contacts():
    user_id = get_jwt_identity()
    search_term = request.args.get('query', '')
    sort_by = request.args.get('sort_by', 'name')
    order = request.args.get('order', 'asc')

    contacts_query = Contacts.query.filter_by(user_id=user_id)

    if search_term:
        pattern = f"%{search_term}%"
        contacts_query = contacts_query.filter(
            (Contacts.name.ilike(pattern)) | (Contacts.email.ilike(pattern))
        )

    if sort_by in ['name', 'created_at']:
        contacts_query = contacts_query.order_by(
            getattr(Contacts, sort_by).desc() if order == 'desc' else getattr(Contacts, sort_by).asc()
        )

    contacts = contacts_query.all()
    return jsonify([contact.to_dict() for contact in contacts])


if __name__ == '__main__':
    app.run(debug=True)
