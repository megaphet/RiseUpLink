# Quick Start: Testing Contact Management System

## Start the App
```bash
cd RiseUpLink
.\.venv311\Scripts\python app.py
```
App runs at: http://127.0.0.1:5000

## Test Scenario 1: Youth Registration & Preferences

### Step 1: Register as a New Youth
1. Go to http://127.0.0.1:5000/register
2. Fill in:
   - Full Name: "John Doe"
   - Email: "john@example.com"
   - Phone: "+256701111111"
   - WhatsApp: "+256701111111"
   - Password: "password123"
   - Role: "Youth"
   - Preferred Contact: **WhatsApp** (select the radio button)
3. Click "Register"

### Step 2: Create Youth Profile
1. Log in with john@example.com / password123
2. Click "Create Profile" button
3. Fill in:
   - Category: "Refugee"
   - Country: "Uganda"
   - Community: "Bidi Bidi Camp"
   - WhatsApp Number: "+256701111111"
   - Preferred Feedback: **Email** (to see how preferences differ from registration)
4. Click "Create Profile"
5. You're now a youth with email preference for application feedback!

### Step 3: Update Contact Preferences
1. Click user dropdown (👤 John Doe) → "Profile & Contact Settings"
2. Verify current settings are displayed
3. Change WhatsApp preference to **WhatsApp**
4. Click "Save Changes"
5. Refresh and verify changes persisted

## Test Scenario 2: Donor Posts Opportunity & Sends Notification

### Step 1: Log in as Donor
1. Go to http://127.0.0.1:5000/login
2. Email: "donor@example.com"
3. Password: "password"

### Step 2: Post an Opportunity (if not already created)
1. Click "Dashboard" → "Post Opportunity"
2. Fill in opportunity details
3. Submit

### Step 3: View Applications
1. Click "Dashboard" → "Manage Opportunities & Applications"
2. You should see opportunities with application counts

### Step 4: Update Application Status
1. Find an opportunity with applications
2. Click "View Applications"
3. Select a status (e.g., "Offered") from the dropdown
4. Click "Update Status"
5. **Watch the console logs** - you should see notification logged

```
EMAIL (console) -> To: john@example.com Subject: Application Status Update: ...
```

or

```
WhatsApp sent to +256701111111 (SID: ...)
```

## Test Scenario 3: Multi-user Contact Setup

### Login as Different Roles:
```
Admin:      admin@example.com / password (preferred: whatsapp)
Donor:      donor@example.com / password (preferred: email)
Field:      field@example.com / password (preferred: whatsapp)
Youth:      youth@example.com / password (preferred: email for feedback)
```

### For Each User:
1. Go to Profile & Contact Settings
2. Verify their contact information
3. Note their preferred methods
4. Try updating contact info (e.g., change phone number)

## Test Scenario 4: Public Contact Page

1. Go to http://127.0.0.1:5000/contact
2. **No login required** - page is public
3. You should see:
   - Admin's email: admin@example.com
   - Admin's WhatsApp: +256701234567 (clickable link)
   - Admin's Phone: +256701234567
   - FAQ section with common questions
4. Click the WhatsApp link - it should open WhatsApp (if installed)

## Test Scenario 5: Email vs WhatsApp Notifications

### Setup Two Youth Accounts:

**Youth A - Email Preference:**
- Register with email feedback preference
- Create profile with email preference
- Apply to an opportunity

**Youth B - WhatsApp Preference:**
- Register with WhatsApp preference
- Create profile with WhatsApp preference
- Apply to an opportunity

### Then as Donor:
1. Update both applications to "Offered"
2. Watch console output - should see BOTH:
   - Email notification for Youth A
   - WhatsApp notification for Youth B

Expected console output:
```
EMAIL (console) -> To: youth-a@example.com Subject: Application Status Update: ...
WhatsApp sent to +256702222222 (SID: ...)
```

## Test Scenario 6: Fallback Behavior

### Test: Youth with WhatsApp preference but no WhatsApp number

1. Register youth with whatsapp preference
2. Create profile **WITHOUT** filling in WhatsApp number
3. Have donor update their application status
4. **Should fall back to email notification**

Check console:
```
EMAIL (console) -> To: [youth-email] Subject: Application Status Update: ...
```

## Key Components to Verify

### ✅ Database Schema
- Login to app, check if users can register with new fields
- Profile settings page loads without errors
- Data persists after page refresh

### ✅ Registration Form
- All new fields appear and accept input
- Radio buttons for preferences work
- Form validation passes

### ✅ Profile Settings Page
- Accessible from dropdown menu
- Shows current values pre-filled
- Updates save correctly
- Different for youth (shows feedback preference)

### ✅ Contact Page
- Accessible without login
- Shows admin contact info
- FAQ section displays properly
- WhatsApp link format is correct

### ✅ Notifications
- Watch console logs when application status changes
- For email: "EMAIL (console) -> To: ..."
- For WhatsApp: "WhatsApp sent to ..."
- Respects user's preferred_feedback setting

### ✅ Navigation
- "Contact" link in navbar
- User dropdown with profile option
- Profile settings accessible from dashboard

## Troubleshooting

### Issue: "preferred_feedback not found" error
**Solution**: Database was not properly migrated. Delete riseup.db and reseed:
```bash
Remove-Item riseup.db -Force
.\.venv311\Scripts\python seed.py
```

### Issue: Profile Settings page shows error
**Solution**: Ensure you're logged in. If error persists:
1. Check app.py has `/profile/settings` route
2. Check profile_settings.html template exists
3. Check app console for error details

### Issue: Contact page shows "No admin contact info"
**Solution**: At least one admin must exist in database. Run seed.py to create test admin.

### Issue: Notifications not appearing in console
**Solution**: 
1. Make sure app is running (check Flask terminal)
2. Check Flask running at http://127.0.0.1:5000
3. Update application status - notification prints immediately
4. Check for errors in app console

## Files to Reference

- **Models**: `models.py` - User and YouthProfile schema
- **Routes**: `app.py` - `/profile/settings`, `/contact`
- **Notifications**: `notifications.py` - notify_applicant() function
- **Templates**: 
  - `templates/profile_settings.html` - settings form
  - `templates/contact.html` - contact/FAQ page
  - `templates/register.html` - registration with contact fields
  - `templates/create_profile.html` - profile with feedback preference
- **Documentation**: `CONTACT_MANAGEMENT.md` - full documentation

## Next Steps

Once testing is complete, consider:
1. Setting up SMTP for real email notifications
2. Setting up Twilio account for WhatsApp notifications
3. Creating more test data with varied preferences
4. Testing actual email/WhatsApp deliverability
5. Verifying notification timing and formatting
