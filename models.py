from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import uuid
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()


class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)  # Indexed for faster lookups
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    oauth_provider = db.Column(db.String(50), nullable=True)  # 'google', 'github', etc.
    oauth_id = db.Column(db.String(255), unique=True, nullable=True)  # Unique OAuth user ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contacts = db.relationship('Contacts', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "oauth_provider": self.oauth_provider,
            "created_at": self.created_at.isoformat()
        }


class Contacts(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    categories = db.Column(db.JSON, default=[])  # Keep JSON if using PostgreSQL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, index=True)  # Indexed for better performance

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "categories": self.categories,
            "created_at": self.created_at.isoformat(),
            "user_id": str(self.user_id)
        }
