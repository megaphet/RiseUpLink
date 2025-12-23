# Quick Reference: Contact Management System

## 🎯 What's New

**Users can now:**
- ✅ Provide phone & WhatsApp numbers during registration
- ✅ Choose preferred notification method (Email or WhatsApp)  
- ✅ Youth choose how to receive application feedback
- ✅ Update contact info anytime in Profile Settings
- ✅ View admin's contact info on public Contact page

**Donors can:**
- ✅ Send notifications that respect youth's preference
- ✅ All updates automatically go via youth's chosen method

## 📋 Test Users (Password: `password`)

| Email | Role | Phone | WhatsApp | Pref Contact |
|-------|------|-------|----------|--------------|
| admin@example.com | Admin | +256701234567 | +256701234567 | whatsapp |
| donor@example.com | Donor | +256702345678 | +256702345678 | email |
| field@example.com | Field | +256703456789 | +256703456789 | whatsapp |
| youth@example.com | Youth | +256704567890 | +256704567890 | email (feedback) |

## 🔗 Key URLs

| Page | URL | Notes |
|------|-----|-------|
| Register | `/register` | New: Contact fields + preference |
| Login | `/login` | Same as before |
| Dashboard | `/dashboard` | Same as before |
| Create Profile | `/create_profile` | New: Feedback preference |
| Profile Settings | `/profile/settings` | **NEW** - Update contact info |
| Contact Page | `/contact` | **NEW** - Admin info & FAQ |

## 📝 Registration Form (New Fields)

```
[Basic Info]
- Full Name (required)
- Email (required)
- Password (required)
- Role (required)

[Contact Information]
- Phone Number (optional, with country code)
- WhatsApp Number (optional)
- Preferred Contact Method (radio buttons)
  ○ Email (default)
  ○ WhatsApp
```

## 👤 Profile Settings Page

**Accessible from**: User dropdown → "Profile & Contact Settings"

**Fields you can update:**
- Phone Number
- WhatsApp Number  
- Preferred Contact Method (email/whatsapp)
- **For Youth Only**: Application Feedback Preference

## 🧑‍🤝‍🧑 Youth Profile Creation (New Fields)

```
[Profile Info - Same as before]
- Category
- Country
- Community

[New: Contact & Notification]
- WhatsApp Number (optional)
- Application Feedback Preference (radio buttons)
  ○ Email (default - sent to registered email)
  ○ WhatsApp (faster notifications)
```

## 💬 How Notifications Work

**Donor updates application status** → **System checks youth's preference**

```
If youth chose "WhatsApp":
  → Send via WhatsApp
  → Fallback to Email if no WhatsApp number
  
If youth chose "Email":
  → Send via Email (default)
```

**Console output examples:**
```
EMAIL (console) -> To: youth@example.com Subject: ...
WhatsApp sent to +256704567890 (SID: ...)
```

## 📞 Contact Page (`/contact`)

- **No login required** - Public page
- Shows admin's:
  - Email (clickable mailto link)
  - WhatsApp (clickable wa.me link)
  - Phone number
- FAQ accordion with 4 answers
- Support response times

## 🗄️ Database Schema

### User Model - NEW COLUMNS
```python
whatsapp_number = db.Column(db.String(20))              # User's WhatsApp
preferred_contact = db.Column(db.String(20), default='email')  # email or whatsapp
```

### YouthProfile Model - NEW COLUMNS
```python
whatsapp_number = db.Column(db.String(20))              # Youth's WhatsApp
preferred_feedback = db.Column(db.String(20), default='email')  # email or whatsapp
```

## 🔄 Updated Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/register` | POST | Now captures `whatsapp_number`, `preferred_contact` |
| `/create_profile` | POST | Now captures `whatsapp_number`, `preferred_feedback` |
| `/profile/settings` | GET/POST | **NEW** - View/update contact info |
| `/contact` | GET | **NEW** - Public admin contact & FAQ |
| `/donor/application/<id>/update` | POST | Now uses preference-aware notifications |

## 🧪 Quick Test Scenario

1. **Register**: Go to `/register` with new contact fields
2. **Login**: Use registered credentials
3. **Create Profile**: Add feedback preference
4. **Go to Settings**: Click user dropdown → Profile Settings
5. **Update Preferences**: Change phone/WhatsApp
6. **Check Contact**: View `/contact` page
7. **Test Notification**: As donor, update application status → check console

## 📊 Files Changed

### Created (4 files)
- `templates/profile_settings.html` - Settings page
- `templates/contact.html` - Contact/FAQ page
- `CONTACT_MANAGEMENT.md` - Full documentation
- `TESTING_CONTACT_SYSTEM.md` - Testing guide

### Modified (7 files)
- `models.py` - Added contact columns
- `app.py` - New routes, updated existing routes
- `notifications.py` - Preference-aware notifications
- `seed.py` - Test data with contact info
- `templates/register.html` - Contact fields
- `templates/create_profile.html` - Feedback preference
- `templates/base.html` - Contact link + user dropdown

## ⚙️ Optional Configuration

For **real** email/WhatsApp (not console):

```bash
# Email (SMTP)
set MAIL_SERVER=smtp.gmail.com
set MAIL_PORT=587
set MAIL_USERNAME=your-email@gmail.com
set MAIL_PASSWORD=your-app-password

# WhatsApp (Twilio)
set TWILIO_ACCOUNT_SID=your-sid
set TWILIO_AUTH_TOKEN=your-token
set TWILIO_PHONE_FROM=+1234567890
```

Without these, notifications print to console (for testing).

## ✅ Verification Checklist

- [ ] App runs without errors: `.\.venv311\Scripts\python app.py`
- [ ] Registration shows new contact fields
- [ ] Profile Settings page loads and updates work
- [ ] Contact page displays admin info
- [ ] User dropdown shows profile link
- [ ] Donor can update application status
- [ ] Console shows notification logs
- [ ] Contact page has FAQ visible
- [ ] WhatsApp links are clickable
- [ ] All navigation links work

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "No such column" error | Delete riseup.db and reseed: `python seed.py` |
| Profile Settings blank | Ensure logged in; check app console for errors |
| No admin on Contact page | Run `python seed.py` to create test admin |
| Notifications not in console | Update application status - logs appear immediately |
| WhatsApp link broken | Check phone number format (+countrycode....) |

## 📚 Documentation

- **Full Details**: `CONTACT_MANAGEMENT.md`
- **Step-by-Step Testing**: `TESTING_CONTACT_SYSTEM.md`
- **Implementation Notes**: `IMPLEMENTATION_SUMMARY.md`

## 🎓 Key Concepts

**Preferred Contact** (User level):
- How platform contacts YOU about account matters
- Set at registration, updateable in Profile Settings

**Preferred Feedback** (Youth level):
- How DONORS contact YOU about application status
- Set when creating profile, updateable in Profile Settings

**Notification Flow**:
1. Donor updates application status
2. System reads youth's `preferred_feedback`
3. Sends notification via chosen method
4. Falls back gracefully if needed

## 🚀 Get Started

```bash
# Terminal 1: Start Flask app
.\.venv311\Scripts\python app.py
# App runs at http://127.0.0.1:5000

# Then in browser:
# Register → Create Profile → Update Settings → Test Notifications
```

**See TESTING_CONTACT_SYSTEM.md for detailed test scenarios!**
