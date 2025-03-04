from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# JSON file path
DB_FILE = 'contacts.json'

# Initialize empty contacts list if file doesn't exist
def get_contacts_data():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump([], f)
        return []
    
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# Save contacts to JSON file
def save_contacts_data(contacts):
    with open(DB_FILE, 'w') as f:
        json.dump(contacts, f, indent=4)

# Routes
@app.route("/")
def home():
    return "Flask is running successfully!"

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    contacts = get_contacts_data()
    return jsonify(contacts)

@app.route('/api/contacts/<string:id>', methods=['GET'])
def get_contact(id):
    contacts = get_contacts_data()
    contact = next((c for c in contacts if c['id'] == id), None)
    
    if contact is None:
        return jsonify({'error': 'Contact not found'}), 404
        
    return jsonify(contact)

@app.route('/api/contacts', methods=['POST'])
def create_contact():
    data = request.json
    
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({'error': 'Name and email are required'}), 400
    
    contacts = get_contacts_data()
    
    new_contact = {
        'id': str(uuid.uuid4()),
        'name': data['name'],
        'email': data['email'],
        'phone': data.get('phone', ''),
        'categories': data.get('categories', []),
        'created_at': datetime.now().isoformat()
    }
    
    contacts.append(new_contact)
    save_contacts_data(contacts)
    
    return jsonify(new_contact), 201

@app.route('/api/contacts/<string:id>', methods=['PUT'])
def update_contact(id):
    contacts = get_contacts_data()
    contact_index = next((i for i, c in enumerate(contacts) if c['id'] == id), None)
    
    if contact_index is None:
        return jsonify({'error': 'Contact not found'}), 404
        
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    contact = contacts[contact_index]
    contact['name'] = data.get('name', contact['name'])
    contact['email'] = data.get('email', contact['email'])
    contact['phone'] = data.get('phone', contact['phone'])
    contact['categories'] = data.get('categories', contact.get('categories', []))
    
    save_contacts_data(contacts)
    
    return jsonify(contact)

@app.route('/api/contacts/<string:id>', methods=['DELETE'])
def delete_contact(id):
    contacts = get_contacts_data()
    initial_length = len(contacts)
    
    contacts = [c for c in contacts if c['id'] != id]
    
    if len(contacts) == initial_length:
        return jsonify({'error': 'Contact not found'}), 404
        
    save_contacts_data(contacts)
    
    return jsonify({'message': f'Contact {id} deleted successfully'})

if __name__ == '__main__':
    app.run(debug=True)



# going over the backend concepts
# deploying on a server
# ci/cd
# update
# search using contact
# the search should be case insensitive
# displaying in grid or list
# displaying in dark mode
# add country code
# sort by category
# sort by name / aphabetical
# display of cards in grid mode
# add images to each contact card
# signing in with google or github
# writing tests
# search bar redesign