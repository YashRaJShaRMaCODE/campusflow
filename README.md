# CampusFlow API

A sample Django REST API for recording student marks and viewing class summaries. Student-data endpoints require a signed-in staff account. The public root and health check expose no student information.

The product overview is available at `/product/`. Its report visual is synthetic. Never put real student details into the demo. An opt-in mailing form appears only when `LEADHUB_BASE_URL` is set to the deployed HTTPS LeadHub origin; a separate unchecked option requests related products using only the product ID after consent. The product page CSP permits requests only to the configured origin.

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

Sign in at `http://127.0.0.1:8000/api-auth/login/`. Local development uses SQLite and a development-only secret. For deployment, set `DJANGO_DEBUG=false`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and a PostgreSQL `DATABASE_URL` in the host's secret settings. Production refuses to start with SQLite or a PostgreSQL URL that disables TLS; `sslmode=require` is used if the URL omits `sslmode`. URL-encode special characters in database usernames and passwords.

For a local demo, sign in to Django admin, create a school, then assign each staff account one `SchoolMembership`. Staff without a school assignment cannot use student-data endpoints. One staff account belongs to one school in this version; there is no public school signup.

## API

The root `GET /` lists endpoint links. `GET /healthz/` is a minimal public health check. All `/students/` endpoints require a signed-in session; create staff users through Django's admin or `createsuperuser`.

| Method | Path | What it does |
| --- | --- | --- |
| `POST` | `/students/add/` | Add a record (`name`, `total_marks`, `marks_obtained`, `date`) |
| `GET` | `/students/` | List records, 25 per page (maximum 100); supports name search, ordering, `date_from`, `date_to`, `min_percentage`, and `max_percentage` filters |
| `GET` | `/students/export.csv` | Download the school-scoped, filtered result set as a private CSV; formula-like names are escaped and the response is not cached |
| `GET` | `/students/exports/` | Review this school's paginated export requests (staff actor, request time and row count; no student details) |
| `GET`, `PUT`, `PATCH` | `/students/{id}/` | View or correct one record; deletion is not exposed |
| `GET` | `/students/{id}/changes/` | View the latest 25 school-scoped change events; includes actor ID, action, record ID and time, never student field values |
| `GET` | `/students/average/` | Class record count and average marks/percentage |
| `GET` | `/students/count/` | Count records with at least 33% |
| `GET` | `/students/summary/` | One school-scoped aggregate with record count, average marks/percentage, and count at or above 33%; no student details |

Example create request:

```json
{
  "name": "Asha Sharma",
  "total_marks": 100,
  "marks_obtained": 82,
  "date": "2026-11-01"
}
```

Names are trimmed and required. Total marks must be positive and obtained marks cannot exceed the total, including when only one field is changed. Record responses include a calculated `percentage` rounded to two decimal places. Date filters use `YYYY-MM-DD`; percentage bounds must be from 0 to 100. Responses for lists use the standard paginated shape with `count`, `next`, `previous`, and `results`.

CSV exports use the same school boundary, search, ordering, date, and percentage filters as the list endpoint. Export requests are logged per school without storing student names or marks. Treat downloaded files as private student data and store or share them only with school authorization.

## Checks

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
python -m compileall -q config students
```

## Privacy and deployment

Do not store real student records in a public demo. Student list, detail, create and summary APIs are scoped to the signed-in staff member's school; client-supplied school IDs are never used. Existing records without an assigned school are hidden from these APIs until an administrator assigns them. This is a basic tenant boundary, not a complete school privacy or compliance program.

The app supports PostgreSQL for deployment, but SQLite on an ephemeral free host is not a durable or backed-up student-data store. Before any real student records are used, configure a managed PostgreSQL database with tested backups and restore, HTTPS, least-privilege access, retention/deletion controls and a privacy/legal review. Keep secrets out of source control. The public health endpoint intentionally returns only `{"status":"ok"}`.

## Service readiness

This repository is a backend API sample; it has no school onboarding UI, staff roles beyond school membership, subscription billing or verified customers. Record create/update actions now write a school-scoped change event in the same database transaction. Events omit names, marks and changed values; read activity, retention controls and compliance review remain outstanding. A possible paid direction is a managed API for individual schools, but it is not ready to sell or use with real student records. Free infrastructure from `free-for.dev` is suitable for CI or synthetic demos only here; do not place student data on a free database or sleeping demo host.
