# Couplendar Backend (Django + DRF + JWT)

## Stack
- Django
- Django REST Framework
- SimpleJWT
- django-cors-headers
- Neon PostgreSQL (via `DATABASE_URL` only)
- Google Places API New (via `GOOGLE_PLACES_API_KEY`)

## Setup
1. `cd backend`
2. `python3.12 -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. Copy `.env.example` values into your environment, including `DATABASE_URL` and `GOOGLE_PLACES_API_KEY`.
6. `python manage.py migrate`
7. `python manage.py runserver`

## Discovery Jobs
Run discovery ingestion manually with management commands.

1. `python manage.py seed_trending_locations --max-per-type 3 --city "Calgary, AB"`
2. `python manage.py ingest_featured_spots`
3. `python manage.py sync_place_enrichment`

Notes:
- Discovery suggestions are based on Google Maps place signals: rating, review volume, summaries, type/category fit, amenities, open-now status, price level, photos, and Maps links.
- Places API New uses field masks for Text Search and Place Details. Adding fields can change Google Maps Platform billing, so keep masks limited to fields rendered by the app.

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
