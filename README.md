# Student Records API

A small Django REST API for recording student marks and viewing class summaries. Student records are private: every student-data endpoint requires a signed-in staff account. The public root and health check expose no student information.

## Run locally

Requires Python 3.12 or newer.

```powershell
git clone https://github.com/YashRaJShaRMaCODE/student-management-system.git
cd student-management-system
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Sign in at `http://127.0.0.1:8000/api-auth/login/`. Local development uses SQLite and a development-only secret. For deployment, set a private `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=false`, and set `DJANGO_ALLOWED_HOSTS` to comma-separated host names. Use a persistent production database or persistent storage; the local SQLite file is ignored by Git and is not a production backup.

## API

The root `GET /` lists endpoint links. `GET /healthz/` is a minimal public health check. All `/students/` endpoints require a signed-in session; create staff users through Django's admin or `createsuperuser`.

| Method | Path | What it does |
| --- | --- | --- |
| `POST` | `/students/add/` | Add a record (`name`, `total_marks`, `marks_obtained`, `date`) |
| `GET` | `/students/` | List records, 25 per page (maximum 100); supports `search` by name and `ordering` by name, date, or marks |
| `GET` | `/students/average/` | Class record count and average marks/percentage |
| `GET` | `/students/count/` | Count records with at least 33% |

Example create request:

```json
{
  "name": "Asha Sharma",
  "total_marks": 100,
  "marks_obtained": 82,
  "date": "2026-11-01"
}
```

Names are trimmed and required. Total marks must be positive and obtained marks cannot exceed the total. Responses for lists use the standard paginated shape with `count`, `next`, `previous`, and `results`.

## Checks

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
python -m compileall -q config students
```

## Privacy and deployment

Do not store real student records in a public demo. Keep secrets out of source control and use HTTPS in production. Configure a durable database, backups, and access only for authorized staff before using real data. The public health endpoint intentionally returns only `{"status":"ok"}`.
