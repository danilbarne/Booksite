from datetime import datetime

from flask_login import UserMixin

from extensions import db


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    verified = db.Column(db.Boolean, default=False)

    verification_code = db.Column(db.String(255))

    code_expires = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)