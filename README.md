# RiseUp Link — MVP

This is a minimal Flask-based MVP for the RiseUp Link verified opportunity platform described in the SRS.

Quick start (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

Email configuration (optional)

To enable real email notifications, set these environment variables or add to `app.config` before starting the app:

- `MAIL_SERVER` (e.g. smtp.gmail.com)
- `MAIL_PORT` (default 587)
- `MAIL_USE_TLS` (True/False)
- `MAIL_USERNAME` (SMTP username)
- `MAIL_PASSWORD` (SMTP password)
- `MAIL_FROM` (optional, default `noreply@riseuplink.local`)

If email is not configured the app will log outgoing messages to the application logger (console).

Seeding sample data

Run the included `seed.py` to create sample users, a youth profile, a verified record, one opportunity, and one application for quick testing:

```powershell
python seed.py
```

