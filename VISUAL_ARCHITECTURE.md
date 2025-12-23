# Contact Management System - Visual Flows & Architecture

## 🔄 Data Flow Diagrams

### 1. Registration & Profile Setup Flow

```
┌─────────────────────┐
│   User Registers    │
└──────────┬──────────┘
           │
           ├─→ Captures:
           │   • Email, Password, Name, Role
           │   • Phone Number (optional)
           │   • WhatsApp Number (optional)
           │   • Preferred Contact: Email/WhatsApp
           │
           ↓
┌─────────────────────────┐
│  User Created in DB     │
│  (with contact prefs)   │
└──────────┬──────────────┘
           │
           ├─→ If Role = YOUTH:
           │   └─→ Redirect to Create Profile
           │
           ├─→ If Role = DONOR/FIELD/ADMIN:
           │   └─→ Account Ready
           │
           ↓
  ┌─────────────────────────┐
  │  Create Youth Profile   │
  └──────────┬──────────────┘
             │
             ├─→ Captures:
             │   • Category, Country, Community
             │   • WhatsApp Number (optional)
             │   • Preferred Feedback: Email/WhatsApp ⭐
             │
             ↓
  ┌──────────────────────────────────┐
  │  YouthProfile Created            │
  │  (with feedback preference)      │
  └──────────┬───────────────────────┘
             │
             ↓
  ┌──────────────────────────────────┐
  │  Youth Ready to Apply            │
  │  for Opportunities               │
  └──────────────────────────────────┘
```

### 2. Application Status Notification Flow

```
┌────────────────────────────┐
│  Donor Views Applications  │
└──────────────┬─────────────┘
               │
               ↓
    ┌──────────────────────────┐
    │ Donor Updates Status:    │
    │ UnderReview/Offered/etc  │
    └──────────┬───────────────┘
               │
               ↓
    ┌──────────────────────────────┐
    │  POST /donor/application/<id>/update
    │  (update application status) │
    └──────────┬───────────────────┘
               │
               ↓
    ┌──────────────────────────────┐
    │  notify_applicant() called   │
    │  with youth_user, title,     │
    │  new_status                  │
    └──────────┬───────────────────┘
               │
               ↓
    ┌─────────────────────────────────┐
    │  Check: youth.youth_profile.    │
    │         preferred_feedback      │
    └──────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ↓ 'whatsapp'  ↓ 'email'
     ┌──────────┐  ┌─────────────┐
     │ Send via │  │  Send via   │
     │ WhatsApp │  │  Email      │
     └──────────┘  └─────────────┘
        │              │
        └──────┬───────┘
               │
        ┌──────↓──────────────┐
        │  Log Notification   │
        │  to Console/Logger  │
        └─────────────────────┘
```

### 3. Profile Settings Update Flow

```
┌────────────────────────────────────┐
│  User at Dashboard                 │
│  Clicks: 👤 Name → Settings        │
└──────────┬─────────────────────────┘
           │
           ↓
┌────────────────────────────────────┐
│  GET /profile/settings             │
│  (loads current contact info)      │
└──────────┬─────────────────────────┘
           │
           ↓
┌────────────────────────────────────┐
│  Display Profile Settings Form:    │
│  • Phone Number                    │
│  • WhatsApp Number                 │
│  • Preferred Contact (E-mail/WA)   │
│  • [YOUTH] Feedback Preference     │
└──────────┬─────────────────────────┘
           │
           ├─→ User updates fields
           │
           ↓
┌────────────────────────────────────┐
│  POST /profile/settings            │
│  (submit updated form)             │
└──────────┬─────────────────────────┘
           │
           ↓
┌────────────────────────────────────┐
│  Update current_user:              │
│  • phone_number                    │
│  • whatsapp_number                 │
│  • preferred_contact               │
│  (Save to database)                │
└──────────┬─────────────────────────┘
           │
           ├─→ If YOUTH:
           │   └─→ Update YouthProfile:
           │       • whatsapp_number
           │       • preferred_feedback
           │
           ↓
┌────────────────────────────────────┐
│  Flash: "Changes saved"            │
│  Redirect to /profile/settings     │
└────────────────────────────────────┘
```

## 🗂️ Database Schema Diagram

```
User Table
─────────────────────────────────────
│ id (PK)
│ email (unique)
│ password_hash
│ full_name
│ phone_number ⭐ NEW
│ whatsapp_number ⭐ NEW
│ preferred_contact ⭐ NEW (enum: email/whatsapp)
│ role (enum: youth/donor/admin/field)
│ created_at
└─→ RELATES TO: YouthProfile (if role=youth)


YouthProfile Table
──────────────────────────────────────
│ id (PK)
│ user_id (FK → User)
│ full_name
│ phone_number
│ whatsapp_number ⭐ NEW
│ preferred_feedback ⭐ NEW (enum: email/whatsapp)
│ category
│ country
│ community
│ verification_status
│ profile_completed
└─→ RELATES TO: User (1-to-1)
    └─→ RELATES TO: Application (1-to-many)


Application Table
──────────────────────────────────────
│ id (PK)
│ opportunity_id (FK)
│ youth_id (FK → YouthProfile) ⭐ Uses for notification preference
│ submitted_at
│ status (enum: Submitted/UnderReview/Offered/NotSelected)
│ notes
└─→ RELATES TO: YouthProfile (many-to-1)
    └─→ Uses: YouthProfile.preferred_feedback
```

## 🎨 UI Component Layout

### Navigation Bar
```
┌──────────────────────────────────────────────────────────────┐
│ RiseUp Link  │ Home │ About │ Features │ Media │ Contact │    │
│              │      │       │        │       │        │      │
│              │      │       │        │       │        │ 👤 John │
│              │      │       │        │       │        │ ├─ Profile Settings │
│              │      │       │        │       │        │ ├─ [Verify Recs]   │
│              │      │       │        │       │        │ └─ Logout          │
│              │      │       │        │       │        │                    │
│              └─────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────┘
```

### Registration Form
```
┌─────────────────────────────────────────────────┐
│          REGISTER FOR RISEUP LINK               │
├─────────────────────────────────────────────────┤
│ BASIC INFORMATION                               │
│ ┌────────────────────────────────────────────┐  │
│ │ Full Name: [___________________]           │  │
│ │ Email: [_____________________@_____]       │  │
│ │ Password: [____________________]           │  │
│ │ Role: ◇ Youth                              │  │
│ │       ◇ Donor/NGO ◇ Field ◇ Admin         │  │
│ └────────────────────────────────────────────┘  │
│                                                 │
│ CONTACT INFORMATION                             │
│ ┌────────────────────────────────────────────┐  │
│ │ Phone: [+256_______________]                │  │
│ │        (optional, with country code)        │  │
│ │                                             │  │
│ │ WhatsApp: [+256_______________]            │  │
│ │           (optional, same as phone OK)     │  │
│ │                                             │  │
│ │ Preferred Contact Method:                   │  │
│ │ ◉ Email (default)                          │  │
│ │ ◇ WhatsApp                                 │  │
│ │ (for platform notifications)                │  │
│ └────────────────────────────────────────────┘  │
│                                                 │
│  [ Register ]  [ Cancel ]                      │
└─────────────────────────────────────────────────┘
```

### Youth Profile Creation Form
```
┌──────────────────────────────────────────────────────┐
│     COMPLETE YOUR YOUTH PROFILE                      │
├──────────────────────────────────────────────────────┤
│ PROFILE INFORMATION                                  │
│ ┌──────────────────────────────────────────────────┐ │
│ │ Category: [Refugee ▼]                            │ │
│ │ Country: [Uganda___________________]             │ │
│ │ Community: [Bidi Bidi Camp__________]            │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ CONTACT & NOTIFICATION PREFERENCES                  │
│ ┌──────────────────────────────────────────────────┐ │
│ │ WhatsApp Number: [+256_____________]             │ │
│ │                 (optional)                        │ │
│ │                                                   │ │
│ │ How to receive application feedback? ⭐          │ │
│ │ ◉ 📧 Email (default - to your email)            │ │
│ │ ◇ 💬 WhatsApp (faster notifications)             │ │
│ │                                                   │ │
│ │ (Donors will use this method to contact you)    │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│  [ Create Profile ]  [ Cancel ]                     │
└──────────────────────────────────────────────────────┘
```

### Profile Settings Page
```
┌─────────────────────────────────────────────────┐
│   PROFILE & CONTACT SETTINGS                    │
├─────────────────────────────────────────────────┤
│ Full Name: [John Doe] (read-only)               │
│ Email: [john@example.com] (read-only)           │
│                                                 │
│ CONTACT INFORMATION                             │
│ Phone: [+256701111111]                          │
│ WhatsApp: [+256701111111]                       │
│                                                 │
│ COMMUNICATION PREFERENCES                       │
│ Preferred Contact Method:                       │
│ ◇ Email                                         │
│ ◉ WhatsApp ⭐ (You chose this)                  │
│                                                 │
│ ─── IF YOUTH ───────────────────────────────    │
│ APPLICATION FEEDBACK PREFERENCE                 │
│ ◉ Email (default)                              │
│ ◇ WhatsApp                                     │
│ (How donors notify you about app status)       │
│ ─────────────────────────────────────────────   │
│                                                 │
│  [ Save Changes ]  [ Cancel ]                   │
└─────────────────────────────────────────────────┘
```

### Contact Page
```
┌────────────────────────────────────────────────────┐
│            CONTACT & SUPPORT                       │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────┐  ┌──────────────────────┐  │
│  │ 📧 EMAIL SUPPORT │  │ 💬 WHATSAPP SUPPORT  │  │
│  ├──────────────────┤  ├──────────────────────┤  │
│  │ admin@example.com│  │ +256701234567        │  │
│  │ (24-48 hrs)      │  │ (4-6 hrs weekdays)   │  │
│  └──────────────────┘  └──────────────────────┘  │
│                                                    │
│  ┌──────────────────┐  ┌──────────────────────┐  │
│  │ 📱 PHONE SUPPORT │  │ ⏰ RESPONSE TIME     │  │
│  ├──────────────────┤  ├──────────────────────┤  │
│  │ +256701234567    │  │ Email: 24-48 hrs     │  │
│  │ (biz hours)      │  │ WhatsApp: 4-6 hrs    │  │
│  └──────────────────┘  └──────────────────────┘  │
│                                                    │
│ ┌──────────────────────────────────────────────┐  │
│ │ FREQUENTLY ASKED QUESTIONS                   │  │
│ ├──────────────────────────────────────────────┤  │
│ │ ► How do I reset my password?                │  │
│ │   Contact support team via email/WhatsApp    │  │
│ │ ► How do I change preferences?               │  │
│ │   Profile & Contact Settings in dashboard    │  │
│ │ ► Why no notifications?                      │  │
│ │   Update contact info in Profile Settings    │  │
│ │ ► How to apply for opportunity?              │  │
│ │   Browse and click Apply button              │  │
│ └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

## 🔐 Security & Access Control Flow

```
Public Pages (No Login Required)
├─ /                      (Home/Landing)
├─ /about                 (About page)
├─ /features              (Features page)
├─ /media                 (Media gallery)
├─ /contact ⭐ NEW        (Contact & FAQ)
└─ /login                 (Login form)
└─ /register              (Registration form)

Authenticated Pages (Login Required)
├─ /dashboard             (Dashboard - all roles)
├─ /profile/settings ⭐ NEW (Update contact - all roles)
├─ /create_profile        (Create profile - youth only)
├─ /opportunities         (View opportunities - all)
├─ /search_youth          (Search youth - donor/admin)
├─ /upload_documents      (Upload docs - youth)
├─ /donor/applications    (View apps - donor)
│  └─ /donor/opportunity/<id>/edit    (Edit opp)
│  └─ /donor/opportunity/<id>/delete  (Delete opp)
│  └─ /donor/application/<id>/update  (Update status ⭐)
├─ /admin/media ⭐        (Upload media - admin)
├─ /admin/recommendations (Verify recs - admin)
│  └─ /admin/recommendation/<id>/verify
└─ /admin/reports         (View reports - admin)

Data Protection
├─ Users can only update own contact info
├─ Admins can't access other user settings
├─ Contact page is read-only
├─ Youth preferences only visible to youth
└─ Donor can see app preferences when sending notification
```

## 📊 Notification Decision Tree

```
Application Status Update Received
          │
          ↓
    Get Youth User
    Get YouthProfile
          │
          ↓
    Read: youth.youth_profile.preferred_feedback
          │
      ┌───┴────────┐
      │            │
      ↓ 'whatsapp' ↓ 'email'
      │            │
   Check WhatsApp  Send Email
   number exists   to:
      │            youth.email
   ┌──┴─────┐      │
   │        │      │
Yes │       No     Log: "EMAIL..."
   │        │      │
Send│ Fall to Email ↓
WA  │ (attempt)    Success
│   │              │
│   │              ↓
│   └──────┬───────┘
│          │
│          ↓
│     Log: "WhatsApp sent to..."
│     or
│     Log: "Email sent to..."
│
↓
Notification Complete ✓
```

## 🎯 Feature Comparison: Before vs After

| Feature | Before | After |
|---------|--------|-------|
| User Registration | Email, Password, Name, Role | + Phone, WhatsApp, Preferred Contact |
| Contact Options | Email only | Email + WhatsApp |
| Youth Profile | Category, Country, Community | + WhatsApp, + Feedback Preference |
| Notifications | To email always | To email or WhatsApp (youth's choice) |
| Settings Page | None | ✅ New Profile & Contact Settings |
| Public Contact | None | ✅ New Contact & FAQ page |
| User Menu | Logout only | Dropdown: Settings, Verify Recs, Logout |
| Admin Info | None | Shows on public contact page |
| Fallback Behavior | N/A | Graceful (WA→Email) |

## 📍 Route Map

```
REGISTRATION FLOW
/register (GET)  → Show form
  ↓
/register (POST) → Create user with contact info
  ↓
/login → Authenticate
  ↓
IF youth: /create_profile → Create profile with feedback preference
IF donor/admin/field → /dashboard → Ready to use

SETTINGS FLOW
/profile/settings (GET)  → Show current settings
  ↓
/profile/settings (POST) → Update contact info
  ↓
/profile/settings (GET)  → Confirm changes (refresh)

NOTIFICATION FLOW
/donor/applications → View applications
  ↓
/donor/application/<id>/update (POST) → Change status
  ↓
notify_applicant() → Check preference
  ↓
send_email() or send_whatsapp() → Notify youth
  ↓
Log to console → Visible in terminal

PUBLIC PAGES
/contact (GET) → Show admin info & FAQ
  ↓
[No login needed]
```

## 💡 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate `whatsapp_number` field | Some users may have different WhatsApp number |
| `preferred_contact` on User | How platform reaches YOU |
| `preferred_feedback` on YouthProfile | How DONORS reach you (youth-specific) |
| Radio buttons (not checkboxes) | Single choice per preference (simpler) |
| Fallback to email | Always able to reach user |
| Console logging | Works without SMTP/Twilio setup (dev-friendly) |
| Public contact page | Helps users get help without account |
| Dropdown menu | Cleaner navbar, groups user actions |
| Profile settings separate page | Focused UI, easier to update |

This comprehensive visual guide helps understand the architecture, flows, and UI layouts of the new contact management system!
