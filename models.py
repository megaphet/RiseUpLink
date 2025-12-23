from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
# Create SQLAlchemy instance here to avoid circular import with app
db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    whatsapp_number = db.Column(db.String(20))  # For notifications via WhatsApp
    preferred_contact = db.Column(db.String(20), default='email')  # 'email' or 'whatsapp'
    role = db.Column(db.String(20))  # youth, donor, admin, field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class YouthProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    whatsapp_number = db.Column(db.String(20))  # For receiving feedback
    preferred_feedback = db.Column(db.String(20), default='email')  # 'email' or 'whatsapp'
    category = db.Column(db.String(100))
    country = db.Column(db.String(50))
    community = db.Column(db.String(200))
    verification_status = db.Column(db.String(50), default='NotSubmitted')
    profile_completed = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('youth_profile', uselist=False))


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    youth_id = db.Column(db.Integer, db.ForeignKey('youth_profile.id'))
    type = db.Column(db.String(100))
    file_url = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated = db.Column(db.Boolean, default=False)

    youth = db.relationship('YouthProfile', backref=db.backref('documents', lazy=True))


class RecommendationLetter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    youth_id = db.Column(db.Integer, db.ForeignKey('youth_profile.id'))
    issuer_name = db.Column(db.String(200))
    issuer_role = db.Column(db.String(200))
    contact_info = db.Column(db.String(200))
    file_url = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    validated = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    verification_notes = db.Column(db.Text)

    youth = db.relationship('YouthProfile', backref=db.backref('recommendations', lazy=True))


class Verification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    youth_id = db.Column(db.Integer, db.ForeignKey('youth_profile.id'))
    status = db.Column(db.String(50), default='Pending')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    decided_at = db.Column(db.DateTime)
    decided_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)

    youth = db.relationship('YouthProfile', backref=db.backref('verification', uselist=False))
    decider = db.relationship('User', foreign_keys=[decided_by])


class FieldVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    verification_id = db.Column(db.Integer, db.ForeignKey('verification.id'))
    scheduled_at = db.Column(db.DateTime)
    location = db.Column(db.String(300))
    findings = db.Column(db.Text)
    verified_identity = db.Column(db.Boolean)
    completed_at = db.Column(db.DateTime)

    verification = db.relationship('Verification', backref=db.backref('field_visits', lazy=True))


class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    type = db.Column(db.String(100))
    country = db.Column(db.String(50))
    category_target = db.Column(db.String(100))
    description = db.Column(db.Text)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.String(50))
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)

    poster = db.relationship('User', backref=db.backref('opportunities', lazy=True))


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunity.id'))
    youth_id = db.Column(db.Integer, db.ForeignKey('youth_profile.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Submitted')
    notes = db.Column(db.Text)

    opportunity = db.relationship('Opportunity', backref=db.backref('applications', lazy=True))
    youth = db.relationship('YouthProfile', backref=db.backref('applications', lazy=True))


class YouTubeVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    youtube_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(300))
    description = db.Column(db.Text)
    link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_main = db.Column(db.Boolean, default=False)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300))
    message = db.Column(db.Text)
    link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
