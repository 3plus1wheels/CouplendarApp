# Couplendar Backend (Django + DRF + JWT)

## Stack
- Django
- Django REST Framework
- SimpleJWT
- django-cors-headers
- Neon PostgreSQL (via `DATABASE_URL` only)

## Setup
1. `cd backend`
2. `python3.12 -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. Copy `.env.example` values into your environment.
6. `python manage.py migrate`
7. `python manage.py runserver`

## Discovery Jobs
Run discovery ingestion manually with management commands.

1. `python manage.py seed_trending_locations --max-per-type 3 --city "Calgary, AB"`
2. `python manage.py ingest_tiktok_spots`
3. `python manage.py sync_place_enrichment`

Notes:
- `playwright-stealth` requires `pkg_resources`, so the backend pins `setuptools<81`.
- Python 3.14 currently fails to build `greenlet` on macOS/arm64.

## API Endpoints
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`
- `GET /api/profile/`
- `PATCH /api/profile/`

## Register Request Example
```json
{
  "email": "test@example.com",
  "password": "StrongPassword123!",
  "display_name": "Hoang"
}
```

## Register/Login Response Example
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "display_name": "Hoang",
    "first_name": "",
    "last_name": "",
    "city": "",
    "profile_photo": null
  }
}
```
