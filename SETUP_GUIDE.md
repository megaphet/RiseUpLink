# RiseUp Link Setup & Configuration Guide

## Quick Start

### 1. Install Dependencies
```powershell
cd "C:\Users\user\Documents\systems Engieering\personalProjects\DengRiseUp\RiseUpLink"
pip install -r requirements.txt
```

### 2. Seed the Database
```powershell
python seed.py
```
This creates test users with phone numbers ready for notifications:
- **Admin**: `admin@example.com` / `password` — phone: +256701234567
- **Donor**: `donor@example.com` / `password` — phone: +256702345678
- **Youth**: `youth@example.com` / `password` — phone: +256704567890
- **Field Agent**: `field@example.com` / `password` — phone: +256703456789

### 3. Start the App
```powershell
python app.py
```
Open http://127.0.0.1:5000/ in your browser.

---

## Email Notifications (SMTP Configuration)

### Setup Gmail (Recommended for Testing)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy the generated 16-character password

3. **Set Environment Variables** (PowerShell):
```powershell
$env:MAIL_SERVER = "smtp.gmail.com"
$env:MAIL_PORT = "587"
$env:MAIL_USE_TLS = "True"
$env:MAIL_USERNAME = "your-email@gmail.com"
$env:MAIL_PASSWORD = "xxxx xxxx xxxx xxxx"  # The 16-char app password
$env:MAIL_FROM = "noreply@riseuplink.local"
```

4. **Optional: Save to PowerShell Profile** (so variables persist across sessions):
```powershell
# Edit your PowerShell profile (or create if doesn't exist)
notepad $PROFILE

# Add these lines:
$env:MAIL_SERVER = "smtp.gmail.com"
$env:MAIL_PORT = "587"
$env:MAIL_USE_TLS = "True"
$env:MAIL_USERNAME = "your-email@gmail.com"
$env:MAIL_PASSWORD = "xxxx xxxx xxxx xxxx"
$env:MAIL_FROM = "noreply@riseuplink.local"

# Save and reload profile
. $PROFILE
```

### Test Email Sending
1. Register a new user or use an existing one
2. Update their application status (donor → application → update status)
3. Check the email inbox — email logs will appear in console if SMTP not configured

---

## WhatsApp Notifications (Twilio)

### Setup Twilio Account

1. **Create a Free Twilio Account**:
   - Go to https://www.twilio.com/try-twilio
   - Sign up and verify your phone number

2. **Get Your Credentials**:
   - Dashboard → Account SID (copy)
   - Dashboard → Auth Token (copy)
   - Messaging → Try it Out → WhatsApp Sandbox
   - Note the sandbox number (e.g., +1234567890)

3. **Opt into WhatsApp Sandbox**:
   - Send a message from your phone to the sandbox number with text: `join <code>`
   - (Code shown in Twilio WhatsApp Sandbox console)

4. **Install Twilio SDK**:
```powershell
pip install twilio
```

5. **Set Environment Variables** (PowerShell):
```powershell
$env:TWILIO_ACCOUNT_SID = "your-account-sid"
$env:TWILIO_AUTH_TOKEN = "your-auth-token"
$env:TWILIO_PHONE_FROM = "+1234567890"  # Sandbox number
```

6. **Optional: Save to PowerShell Profile**:
```powershell
# Edit your PowerShell profile (or create if doesn't exist)
notepad $PROFILE

# Add these lines:
$env:TWILIO_ACCOUNT_SID = "your-account-sid"
$env:TWILIO_AUTH_TOKEN = "your-auth-token"
$env:TWILIO_PHONE_FROM = "+1234567890"
```

### Test WhatsApp Sending
1. Use the seeded youth account: `youth@example.com` / `password`
2. Donor updates application status
3. WhatsApp message sent to +256704567890 (or the phone you verified)
4. Check Twilio Console → Message Logs for delivery status

**Note**: Phone numbers must be in international format (e.g., +256701234567 for Uganda, +1201234567890 for USA).

---

## Phone Number Field in Registration

The registration form now includes an optional **Phone Number** field:
- Displayed during user sign-up
- Used for WhatsApp notifications
- Format: International (e.g., +256701234567)
- Optional (can be left blank for email-only notifications)

### Update Existing Users
If you have existing users and want to add phone numbers manually:

```powershell
# Open Python interactive shell in the project directory
python

# Then run:
from app import app, db
from models import User

with app.app_context():
    user = User.query.filter_by(email='youth@example.com').first()
    user.phone_number = '+256704567890'
    db.session.commit()
    print('Updated user phone number')
```

---

## Application Status Notifications

When a donor updates an application status, the youth receives notifications via:
- **Email** (if email configured and user has email)
- **WhatsApp** (if Twilio configured and user has phone number)
- **Console log** (fallback if neither above configured)

### Supported Application Statuses
- `UnderReview` — Application being reviewed
- `Offered` — Opportunity offered to applicant
- `NotSelected` — Applicant not selected
- `Withdrawn` — Application withdrawn

### Test Notification Flow
1. Log in as `donor@example.com`
2. Go to **Dashboard** → **Manage Opportunities & Applications**
3. Find an application for the STEM Scholarship
4. Change status to "Offered" and click **Update**
5. Check:
   - Console output for email/WhatsApp logs
   - Email inbox (if SMTP configured)
   - Twilio Console → Messages (if WhatsApp configured)

---

## Environment Variables Checklist

### For Email Notifications:
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx
MAIL_FROM=noreply@riseuplink.local
```

### For WhatsApp Notifications:
```
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_FROM=+1234567890
```

### Check Environment Variables (PowerShell):
```powershell
Get-ChildItem env: | Where-Object { $_.Name -like "*MAIL*" -or $_.Name -like "*TWILIO*" }
```

---

## Troubleshooting

### Email Not Sending
- Check SMTP credentials (try them in Gmail first)
- Check console logs for error messages
- Verify `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD` are set
- Gmail: Disable 2FA or use App Password

### WhatsApp Not Sending
- Check Twilio account is active (not in trial restrictions)
- Verify phone number is in sandbox (sent "join <code>" message)
- Check phone format is international (+country-code)
- Verify `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_FROM` are set
- Check Twilio Console for message logs and errors

### Phone Number Not Captured During Registration
- Ensure `phone_number` field is filled in the form
- Check that the phone number is in international format
- Verify it's saved in the database:
```powershell
python
from app import app, db
from models import User
with app.app_context():
    user = User.query.filter_by(email='youth@example.com').first()
    print(user.phone_number)
```

### Database Not Updated
If you updated code but database schema doesn't have new fields, reset and re-seed:
```powershell
# Delete old database
Remove-Item riseup.db

# Re-seed
python seed.py
```

---

## Production Considerations

1. **Change SECRET_KEY** in `app.py` before production
2. **Use environment file** (.env) instead of hardcoding credentials
3. **Enable HTTPS** (Flask development server is HTTP-only)
4. **Use database** other than SQLite (PostgreSQL recommended)
5. **Set up monitoring** for failed notifications
6. **Add rate limiting** to prevent abuse of notification endpoints
7. **Validate phone numbers** before storing (libphonenumber library)

---

## Need Help?

Check console output when starting the app for detailed error messages. Most issues are due to:
- Missing environment variables
- Incorrect SMTP/Twilio credentials
- Phone number format (must include country code)
- Database schema mismatch (reset with `Remove-Item riseup.db`)
