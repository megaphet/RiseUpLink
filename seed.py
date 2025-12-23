"""Seed script to create sample users, profiles, verification, opportunities and an application.

Run with: python seed.py
"""
from app import app, db
from models import User, YouthProfile, Document, RecommendationLetter, Verification, FieldVisit, Opportunity, Application
from datetime import datetime

def seed():
    with app.app_context():
        db.create_all()
        # Clear existing minimal data (use with caution)
        try:
            User.query.delete()
            YouthProfile.query.delete()
            Opportunity.query.delete()
            Application.query.delete()
            Verification.query.delete()
            Document.query.delete()
            RecommendationLetter.query.delete()
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Create users
        admin = User(
            email='admin@example.com', 
            full_name='Admin User', 
            phone_number='+256701234567',
            whatsapp_number='+256701234567',
            preferred_contact='whatsapp',
            role='admin'
        )
        admin.set_password('password')
        
        donor = User(
            email='donor@example.com', 
            full_name='Donor Org', 
            phone_number='+256702345678',
            whatsapp_number='+256702345678',
            preferred_contact='email',
            role='donor'
        )
        donor.set_password('password')
        
        field = User(
            email='field@example.com', 
            full_name='Field Agent', 
            phone_number='+256703456789',
            whatsapp_number='+256703456789',
            preferred_contact='whatsapp',
            role='field'
        )
        field.set_password('password')
        
        youth_user = User(
            email='youth@example.com', 
            full_name='Amina K.', 
            phone_number='+256704567890',
            whatsapp_number='+256704567890',
            preferred_contact='email',
            role='youth'
        )
        youth_user.set_password('password')
        db.session.add_all([admin, donor, field, youth_user])
        db.session.commit()

        # Youth profile
        profile = YouthProfile(
            user_id=youth_user.id, 
            full_name='Amina K.', 
            phone_number='+256704567890',
            whatsapp_number='+256704567890',
            preferred_feedback='email',
            category='Refugee', 
            country='UG', 
            community='Bidi Bidi', 
            profile_completed=True
        )
        db.session.add(profile)
        db.session.commit()

        # Documents and recommendation
        doc = Document(youth_id=profile.id, type='ID', file_url='sample-id.pdf', validated=True, uploaded_at=datetime.utcnow())
        rec = RecommendationLetter(youth_id=profile.id, issuer_name='Camp Chair John D.', issuer_role='Camp Chairman', contact_info='+256-xxx', file_url='sample-rec.pdf', validated=True)
        db.session.add_all([doc, rec])
        db.session.commit()

        # Verification (verified)
        v = Verification(youth_id=profile.id, status='Verified', started_at=datetime.utcnow(), decided_at=datetime.utcnow(), decided_by=admin.id, notes='Docs valid, field verified')
        db.session.add(v)
        db.session.commit()

        # Opportunity posted by donor
        opp = Opportunity(title='STEM Scholarship 2025', type='Scholarship', country='KE', category_target='Refugee', description='Scholarship for refugee youth', posted_at=datetime.utcnow(), deadline='2025-10-15', posted_by=donor.id, is_active=True)
        db.session.add(opp)
        db.session.commit()

        # Application by youth
        application = Application(opportunity_id=opp.id, youth_id=profile.id, submitted_at=datetime.utcnow(), status='Submitted')
        db.session.add(application)
        db.session.commit()

        print('Seed complete. Users: admin@example.com, donor@example.com, field@example.com, youth@example.com (password: password)')
        print('Youth phone: +256704567890 (for WhatsApp testing)')
        print('To test notifications, set environment variables:')
        print('  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_FROM')
        print('Or configure SMTP for email notifications.')

if __name__ == '__main__':
    seed()
