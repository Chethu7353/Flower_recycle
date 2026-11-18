HEAD
# PushpaRecycle

Production-ready Django 5 + DRF web application for recycling temple flower waste into organic fertilizer.

## Features

- Custom email-based user model with Admin, Collector, and Temple Manager roles
- Login, register, logout, forgot password, Google OAuth login via django-allauth
- JWT authentication APIs with refresh tokens
- Temple listing/detail pages with search and city/state filters
- Flower database with quality filters and detailed composting information
- Collection CRUD with status workflow: Pending, Collected, Delivered, Processed
- Admin dashboard cards and Chart.js analytics
- Django Admin customization for users, temples, flowers, and collections
- PostgreSQL configuration through environment variables

## Folder Structure

```text
SIP_website/
  manage.py
  pushparecycle/
    settings.py
    urls.py
    asgi.py
    wsgi.py
  core/
    models.py
    views.py
    api_views.py
    serializers.py
    forms.py
    admin.py
    permissions.py
    migrations/
    management/commands/seed_demo.py
  templates/
    accounts/
    collections/
    dashboard/
    flowers/
    temples/
    base.html
    home.html
  static/
    css/style.css
    js/app.js
  media/
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Create an admin manually if you do not use `seed_demo`:

```bash
python manage.py createsuperuser
```

Demo accounts created by `seed_demo`:

- `admin@pushparecycle.local` / `Admin@12345`
- `collector@pushparecycle.local` / `Collector@12345`
- `manager@pushparecycle.local` / `Manager@12345`

## PostgreSQL

The default `.env.example` uses SQLite so the project runs even if PostgreSQL is not installed.

For PostgreSQL, install/start PostgreSQL, create a database named `pushparecycle`, then update `.env`:

```env
DATABASE_ENGINE=postgres
POSTGRES_DB=pushparecycle
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Google OAuth

1. Create OAuth credentials in Google Cloud Console.
2. Add this redirect URI:
   `http://127.0.0.1:8000/accounts/google/login/callback/`
3. In Django Admin, open `Social applications` and create a Google app with the client ID and secret.
4. Attach it to the default site.

## API Endpoints

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `POST /api/auth/token/refresh/`
- `GET|POST /api/temples/`
- `GET|PUT|PATCH|DELETE /api/temples/{id}/`
- `GET|POST /api/flowers/`
- `GET|PUT|PATCH|DELETE /api/flowers/{id}/`
- `GET|POST /api/collections/`
- `GET|PUT|PATCH|DELETE /api/collections/{id}/`
- `GET /api/dashboard/statistics/`

# Flower_recycle
aa4f3f980575777b90f19ce746a4293fac42ffd0
