# Coderr Backend

REST API for the Coderr freelancer platform, built with Django and Django REST Framework.

## Requirements

- Python 3.13
- Docker (optional)

## Setup (without Docker)

```bash
git clone <repository-url>
cd coderr-backend
python -m venv env
env\Scripts\activate          # Windows
source env/bin/activate       # macOS/Linux
pip install -r requirements.txt
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/`.

## Setup (with Docker)

```bash
cp .env.example .env
docker compose up --build
```

## Project structure

| App | Purpose |
|---|---|
| `core` | Settings and central URL routing |
| `auth_app` | Registration and login |
| `profile_app` | User profiles (business and customer) |
| `offers_app` | Offers and offer details |
| `orders_app` | Orders and order counts |
| `reviews_app` | Reviews |
| `base_info_app` | Aggregated platform statistics |

## Endpoints

TODO: list all endpoints.

## Running tests

TODO
