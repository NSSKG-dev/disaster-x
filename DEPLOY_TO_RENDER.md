# Deploy Disaster X publicly

## What was prepared
- `app.py` — production-ready Flask entry point
- `requirements.txt` — Flask, Requests, Gunicorn
- `Procfile` — production server command
- `render.yaml` — Render configuration

## 1. Put these files in a GitHub repository
Repository root should contain:
- app.py
- requirements.txt
- Procfile
- render.yaml

Do NOT upload `disaster_x.db` if it contains real/personal data.

## 2. Create the Render service
Create a new Web Service from the GitHub repository.

Build command:
`pip install -r requirements.txt`

Start command:
`gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

Health check:
`/api/health`

## 3. Set the admin password
In Render Environment Variables set:
- `DISASTER_X_ADMIN` = your chosen admin username
- `DISASTER_X_PASSWORD` = a strong admin password
- `DISASTER_X_SECRET` = a long random secret (Render can generate it)

## 4. Database note
The app uses SQLite. A free cloud service can have an ephemeral filesystem, so SQLite data should NOT be treated as permanent production storage. For a hackathon demo, it is okay if the service stays running; for a persistent public deployment, attach persistent storage or migrate the reports database to a managed database.

## 5. Test
Open:
`https://YOUR-SERVICE.onrender.com/api/health`

Expected JSON:
`{"ok":true,"app":"Disaster X"}`

Then open the service root URL.
