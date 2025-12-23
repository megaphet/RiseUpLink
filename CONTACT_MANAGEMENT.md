# RiseUp Link - Contact Management System Documentation

## Overview

The RiseUp Link platform now features a comprehensive contact management system that allows all users (youth, donors, field agents, and admins) to manage their contact information and choose their preferred communication methods for notifications.

## Key Features

### 1. **User Contact Information**
Every user can now maintain and update:
- **Phone Number**: Standard phone number (with country code)
- **WhatsApp Number**: Separate WhatsApp contact (can be same or different from phone)
- **Preferred Contact Method**: Users choose between Email or WhatsApp for platform notifications

### 2. **Youth Application Feedback Preference**
Youth applicants can specifically choose how they want to receive application status updates from donors:
- **Email**: Default method - notifications sent to registered email
- **WhatsApp**: Fast notifications via WhatsApp (requires WhatsApp number)

### 3. **Smart Notification System**
The system respects user preferences:
- When a donor updates an application status, the system checks the youth's `preferred_feedback` setting
- Notifications are sent via the youth's chosen method (email or WhatsApp)
- Falls back to email if WhatsApp number is not available
- Logs all notifications for audit purposes

### 4. **Public Contact Page**
A new contact page displays:
- Admin's contact information (email, WhatsApp, phone)
- FAQ section with common questions
- Support response time expectations

## Database Schema Changes

### User Model Updates
```python
class User(db.Model):
    # ... existing fields ...
    phone_number = db.Column(db.String(20))           # Regular phone
    whatsapp_number = db.Column(db.String(20))        # WhatsApp contact
    preferred_contact = db.Column(db.String(20), default='email')  # email or whatsapp
```

### YouthProfile Model Updates
```python
class YouthProfile(db.Model):
    # ... existing fields ...
    whatsapp_number = db.Column(db.String(20))        # Youth's WhatsApp
    preferred_feedback = db.Column(db.String(20), default='email')  # How to receive app updates
```

## User Interface Changes

### Registration Form (templates/register.html)
New fields in registration:
- WhatsApp Number (optional)
- Preferred Contact Method (radio buttons: Email or WhatsApp)

### Youth Profile Creation (templates/create_profile.html)
New fields in profile setup:
- WhatsApp Number (optional)
- Application Feedback Preference (radio buttons: Email or WhatsApp)

### Profile Settings Page (templates/profile_settings.html)
New dedicated page accessible from dashboard:
- Update phone number and WhatsApp number
- Change preferred contact method
- For youth: update application feedback preference
- Clear explanations of how information is used

### Contact Page (templates/contact.html)
New public page at `/contact`:
- Admin's contact information with direct links (email, WhatsApp, phone)
- FAQ section with answers to common questions
- Support response time expectations

### Navigation Updates (templates/base.html)
- Added "Contact" link in main navbar
- Added dropdown user menu with profile/settings access
- Users can access "Profile & Contact Settings" from navbar

## Routes Added

### Profile Management
```
GET  /profile/settings       - View/edit contact information
POST /profile/settings       - Update contact information
GET  /contact                - View admin contact info and FAQ
```

## How It Works

### Registration Flow
1. User registers with email, password, and role
2. Optionally provides phone number and WhatsApp number
3. Selects preferred contact method (email or WhatsApp)
4. Account is created with contact preferences

### Youth Profile Creation
1. Youth creates profile with category, country, community
2. Optionally provides WhatsApp number
3. **Selects preferred feedback method** - how they want to receive application updates
4. Profile is saved with feedback preferences

### Application Status Notification
1. Donor updates application status (UnderReview, Offered, NotSelected)
2. System retrieves youth's `preferred_feedback` from YouthProfile
3. If preference is **WhatsApp**:
   - System uses youth's WhatsApp number from profile
   - Falls back to email if no WhatsApp number exists
4. If preference is **Email** (default):
   - System sends notification to youth's email address
5. Notification is logged with timestamp and recipient

### Profile Settings Update
1. Authenticated user visits Profile & Contact Settings
2. Can update phone number, WhatsApp number, preferred contact method
3. If youth: also updates application feedback preference
4. Changes saved to database immediately

## Code Changes

### notifications.py
Updated `notify_applicant()` function:
```python
def notify_applicant(youth_user, opportunity_title: str, status: str):
    """
    Respects youth's preferred_feedback method (email or whatsapp).
    """
    # Check YouthProfile.preferred_feedback
    preferred_method = youth_user.youth_profile.preferred_feedback
    
    if preferred_method == 'whatsapp':
        # Send via WhatsApp
        send_whatsapp(youth_user.youth_profile.whatsapp_number, message)
    else:
        # Send via Email (default)
        send_email(youth_user.email, subject, body)
```

### app.py
New routes added:
- `/profile/settings` - Profile management
- `/contact` - Public contact/support page

Registration and profile creation updated to capture new fields:
- `whatsapp_number` from form
- `preferred_contact` from radio buttons
- `preferred_feedback` from radio buttons

## Testing

### Test Scenario 1: Email Notifications
1. Register as youth with email preference
2. Create profile with email feedback preference
3. Have donor post opportunity and youth apply
4. Donor updates application status
5. Check email for notification (or console if SMTP not configured)

### Test Scenario 2: WhatsApp Notifications
1. Register as youth with WhatsApp number
2. Create profile with WhatsApp feedback preference
3. Have donor post opportunity and youth apply
4. Donor updates application status
5. Check WhatsApp or console logs

### Test Scenario 3: Profile Update
1. Log in as any user
2. Click user dropdown → "Profile & Contact Settings"
3. Update phone number and WhatsApp number
4. Change preferred contact method
5. If youth: change feedback preference
6. Submit form
7. Verify changes saved (refresh page to confirm)

### Test Scenario 4: Contact Page
1. Navigate to Contact page (public, no login required)
2. View admin contact information
3. See WhatsApp, email, phone links
4. Review FAQ section

## Default Test Users

All test users are seeded with contact information:

| Email | Role | Phone | WhatsApp | Preference | Password |
|-------|------|-------|----------|-----------|----------|
| admin@example.com | Admin | +256701234567 | +256701234567 | whatsapp | password |
| donor@example.com | Donor | +256702345678 | +256702345678 | email | password |
| field@example.com | Field Agent | +256703456789 | +256703456789 | whatsapp | password |
| youth@example.com | Youth | +256704567890 | +256704567890 | email | password |

For youth, they also have:
- `preferred_feedback` = email
- WhatsApp number in profile = +256704567890

## Environment Variables (Optional)

For full notification functionality, configure:

### Email (SMTP)
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@riseuplink.local
```

### WhatsApp (Twilio)
```
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_FROM=+1234567890
```

If not configured, notifications are logged to console for testing.

## Security Considerations

1. **Phone Number Storage**: Phone numbers are stored in plain text (required for Twilio/WhatsApp integration)
2. **WhatsApp Links**: Contact page generates WhatsApp links using `wa.me/` API
3. **User Privacy**: Users can update their own contact info; admins have no special access
4. **Notification Logs**: All sent notifications are logged with recipient info for audit trail

## Future Enhancements

Potential improvements:
1. SMS notifications (in addition to WhatsApp)
2. Notification preferences per message type
3. Notification unsubscribe/opt-out options
4. Bulk contact updates for admins
5. Contact validation via OTP
6. Contact import from CSV (for organizations)

## Troubleshooting

### WhatsApp notifications not sending
- Verify WhatsApp number includes country code (e.g., +256...)
- Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are set
- Check app logs for Twilio error messages

### Email notifications not sending
- Verify SMTP settings in environment
- Check sender email has app password (not regular password for Gmail)
- Check app logs for SMTP connection errors
- Ensure recipient email is valid

### Preference not being applied
- Verify youth profile has `preferred_feedback` set
- Check notification function is called after status update
- Look for errors in app logs

### Contact page shows no admin
- Verify at least one admin user exists in database
- Admin must have contact info filled in profile settings
- Refresh page if admin info appears blank

## Files Modified/Created

### Modified
- `models.py` - Added contact fields to User and YouthProfile
- `app.py` - Added /profile/settings and /contact routes, updated registration
- `notifications.py` - Updated notify_applicant() to respect preferences
- `seed.py` - Updated with contact info for test users
- `templates/register.html` - Added contact fields
- `templates/create_profile.html` - Added feedback preference
- `templates/base.html` - Added Contact link and profile dropdown

### Created
- `templates/profile_settings.html` - Profile management page
- `templates/contact.html` - Public contact/support page

## Summary

The new contact management system provides:
✅ Full control over contact information for all users
✅ Flexible notification preferences (email vs WhatsApp)
✅ Respects youth's choices for application feedback method
✅ Public contact page for support
✅ Seamless integration with existing notification system
✅ Easy profile updates from dashboard
✅ Test-ready with seeded contact data
