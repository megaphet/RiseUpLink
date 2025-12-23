Flask‑Migrate setup and usage

This project now includes Flask‑Migrate integration. Follow these steps to create and apply migrations locally.

1. Install dependencies (run inside your venv):

```bash
pip install Flask-Migrate
```

2. Set `FLASK_APP` and run migrations:

Windows PowerShell:

```powershell
$env:FLASK_APP = 'app.py'
flask db init
flask db migrate -m "create notifications"
flask db upgrade
```

Command Prompt (cmd.exe):

```cmd
set FLASK_APP=app.py
flask db init
flask db migrate -m "create notifications"
flask db upgrade
```

3. Notes:
- If you already have a migrations folder and are using Alembic, create a new revision instead of `init`.
- `db.create_all()` in `app.py` will still create tables when starting the app without migrations, but using Flask‑Migrate is recommended for production and schema changes.
