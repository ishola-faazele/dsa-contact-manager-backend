from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
import os
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from models import User, Contact, db
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# PostgreSQL Configuration
DB_USER = "postgres"
DB_PASSWORD = "bfsp4theFuture1844"
DB_HOST = "localhost"
DB_PORT = "5432"  
DB_NAME = "contactshub-db"

app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_SECRET_KEY'] = "supersecretkey"

db.init_app(app)
migrate = Migrate(app, db)

jwt = JWTManager(app)


# Routes
@app.route("/")
def home():
    return "Flask is running successfully!"

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Name, email, and password are required'}), 400

    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already in use'}), 400

    # Create new user
    new_user = User(name=data['name'], email=data['email'])
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate JWT Token
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token, 'user': user.to_dict()}), 200


@app.route('/api/contacts', methods=['GET'])
@jwt_required()
def get_contacts():
    user_id = get_jwt_identity()
    contacts = Contact.query.filter_by(user_id=user_id).all()
    return jsonify([contact.to_dict() for contact in contacts])

@app.route('/api/contacts/<string:id>', methods=['GET'])
@jwt_required()
def get_contact(id):
    contact = Contact.query.get(id)
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

    new_contact = Contact(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone', ''),
        categories=data.get('categories', []),
        user_id=user_id
    )

    db.session.add(new_contact)
    db.session.commit()

    return jsonify(new_contact.to_dict()), 201


@app.route('/api/contacts/<string:id>', methods=['PUT'])
@jwt_required()
def update_contact(id):
    contact = Contact.query.get(id)
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404

    data = request.json
    contact.name = data.get('name', contact.name)
    contact.email = data.get('email', contact.email)
    contact.phone = data.get('phone', contact.phone)
    contact.categories = data.get('categories', contact.categories)

    db.session.commit()
    return jsonify(contact.to_dict())

@app.route('/api/contacts/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_contact(id):
    user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=id, user_id=user_id).first()

    if not contact:
        return jsonify({'error': 'Contact not found'}), 404

    db.session.delete(contact)
    db.session.commit()

    return jsonify({'message': 'Contact deleted successfully'}), 200


@app.route('/api/contacts/search', methods=['GET'])
@jwt_required()
def search_and_sort_contacts():
    # Get query parameters
    search_term = request.args.get('query', '')
    sort_by = request.args.get('sort_by', 'name')  # default sort field is 'name'
    order = request.args.get('order', 'asc')       # default order is ascending

    # Start building the query on the Contact model
    contacts_query = Contact.query

    # If a search term is provided, filter by name or email (case-insensitive)
    if search_term:
        pattern = f"%{search_term}%"
        contacts_query = contacts_query.filter(
            (Contact.name.ilike(pattern)) | (Contact.email.ilike(pattern))
        )

    # Apply sorting based on the requested sort field and order
    if sort_by == 'name':
        contacts_query = contacts_query.order_by(
            Contact.name.desc() if order == 'desc' else Contact.name.asc()
        )
    elif sort_by == 'created_at':
        contacts_query = contacts_query.order_by(
            Contact.created_at.desc() if order == 'desc' else Contact.created_at.asc()
        )
    # For categories, sorting is more complex because it's stored as JSON.
    # We could, for example, sort by the first element in the JSON array, but that is advanced.

    # Execute the query
    contacts = contacts_query.all()

    # Convert each contact to a dictionary and return as JSON
    return jsonify([contact.to_dict() for contact in contacts])

if __name__ == '__main__':
    app.run(debug=True)



