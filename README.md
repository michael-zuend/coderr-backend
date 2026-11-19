# Coderr Backend

REST API for **Coderr**, a freelancer platform where business users offer
services and customers order and review them. Built with Django and
Django REST Framework.

The frontend is not part of this repository.

## Tech stack

- Python 3.12+
- Django 6.1
- Django REST Framework (token authentication)
- PostgreSQL in Docker, SQLite for local development
- Gunicorn and WhiteNoise in the container
- GitHub Actions for CI and security scans

## Setup without Docker

1. Clone the repository

```bash
git clone https://github.com/michael-zuend/coderr-backend.git
```

```bash
cd coderr-backend
```

2. Create and activate a virtual environment

```bash
python -m venv env
```

Windows:

```bash
env\Scripts\activate
```

macOS/Linux:

```bash
source env/bin/activate
```

3. Install the requirements

```bash
pip install -r requirements.txt
```

4. Create the `.env` file

Windows:

```bash
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

5. Set up the database and the guest users

```bash
python manage.py migrate
```

```bash
python manage.py create_guest_users
```

6. Create an admin user (optional)

```bash
python manage.py createsuperuser
```

7. Start the server

```bash
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000/api/`, the admin panel at
`http://127.0.0.1:8000/admin/`.

### Environment variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key, use a long random string |
| `DEBUG` | `True` for development, `False` for production |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of frontend origins |
| `POSTGRES_DB` | Name of the PostgreSQL database (Docker) |
| `POSTGRES_USER` | PostgreSQL user (Docker) |
| `POSTGRES_PASSWORD` | PostgreSQL password (Docker), use a strong password |
| `CREATE_GUEST_USERS` | `True` creates the guest accounts on container start |

`SECRET_KEY` is required, the app does not start without it. `DEBUG` is
`False` unless it is set to `True`.

By default the frontend is expected at `http://127.0.0.1:5500`
(VS Code Live Server).

### Guest accounts

`python manage.py create_guest_users` creates the guest accounts used by the
guest login of the frontend:

| Username | Password | Type |
|---|---|---|
| `andrey` | `asdasd` | customer |
| `kevin` | `asdasd24` | business |

## Setup with Docker

Docker Desktop must be running.

1. Create the `.env` file

Windows:

```bash
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

2. Build and start the container

```bash
docker compose up --build
```

This starts two containers: the backend and a PostgreSQL database. On
start the backend runs the migrations, collects the static files, creates
the guest users if `CREATE_GUEST_USERS=True` and starts Gunicorn.
The API is available at `http://127.0.0.1:8000/api/`.

3. Stop the container with `Ctrl + C` and remove it with:

```bash
docker compose down
```

After code changes, rebuild the image with `docker compose up --build`.
The database and uploaded files are stored in Docker volumes and survive
restarts. To delete them as well:

```bash
docker compose down -v
```

## Project structure

| App | Purpose |
|---|---|
| `core` | Settings and central URL routing |
| `auth_app` | Registration, login and the guest users command |
| `profile_app` | Profiles of business and customer users |
| `offers_app` | Offers and their basic, standard and premium details |
| `orders_app` | Orders and order counts |
| `reviews_app` | Reviews of business users |
| `base_info_app` | Aggregated platform statistics |

Every app keeps its serializers, views, URLs and permissions in an `api/`
folder.

## Endpoints

All endpoints are prefixed with `/api/`. Authenticated requests need the
header `Authorization: Token <token>`.

| Method | Endpoint | Permission |
|---|---|---|
| POST | `registration/` | public |
| POST | `login/` | public |
| GET, PATCH | `profile/{user_id}/` | authenticated, PATCH only the owner |
| GET | `profiles/business/` | authenticated |
| GET | `profiles/customer/` | authenticated |
| GET | `offers/` | public |
| POST | `offers/` | business users |
| GET | `offers/{id}/` | authenticated |
| PATCH, DELETE | `offers/{id}/` | creator of the offer |
| GET | `offerdetails/{id}/` | authenticated |
| GET | `orders/` | authenticated, only own orders |
| POST | `orders/` | customer users |
| PATCH | `orders/{id}/` | business user of the order |
| GET | `order-count/{business_user_id}/` | authenticated |
| GET | `completed-order-count/{business_user_id}/` | authenticated |
| GET | `reviews/` | authenticated |
| POST | `reviews/` | customer users, one review per business user |
| PATCH, DELETE | `reviews/{id}/` | author of the review |
| GET | `base-info/` | public |

### Query parameters

- `offers/`: `creator_id`, `min_price`, `max_delivery_time`, `search`,
  `ordering` (`updated_at`, `min_price`, prefix `-` for descending),
  `page`, `page_size` (default 6)
- `reviews/`: `business_user_id`, `reviewer_id`, `ordering`
  (`updated_at`, `rating`)

## How the backend works

### Architecture

The project follows a clear separation of responsibilities:

| Layer | File | Responsibility |
|---|---|---|
| Models | `models.py` | Data structure and relations |
| Serializers | `api/serializers.py` | Validation and transformation of data |
| Views | `api/views.py` | API logic |
| URLs | `api/urls.py` | Routing, every app has its own URL file |
| Permissions | `api/permissions.py` | Access control |

All app URLs are included in the central routing in `core/urls.py`.

### Users and profiles

Every user is a Django `User` with a `Profile` of type `business` or
`customer`. The profile is created together with the user during
registration. Name and email are stored on the `User`, all other profile
data on the `Profile`.

### Authentication

The API uses token authentication. Registration and login return a token,
which the frontend sends with every request in the `Authorization` header.
By default every endpoint requires authentication, public endpoints are
marked explicitly.

### Offers

An offer always has exactly three details: `basic`, `standard` and
`premium`. They are created together with the offer in one request. When
an offer is updated, each detail is matched by its `offer_type`, so the
ids of the details stay the same. The offer list is paginated (6 per page)
and returns the lowest price and the shortest delivery time of each offer.

### Orders

A customer orders a single offer detail. The order stores a copy of the
detail data (title, price, features and so on), so later changes to the
offer do not change existing orders. Only the business user of an order can
change its status (`in_progress`, `completed`, `cancelled`).

### Reviews

Only customers can write reviews, and only one review per business user.
Only the author can update or delete a review, and only `rating` and
`description` can be changed.

### Base info

`base-info/` aggregates statistics over the whole platform: number of
reviews, average rating, number of business profiles and number of offers.

## Docker

### Dockerfile

- Uses the slim Python 3.13 image as a base
- Installs the requirements in a separate layer, so they are only
  reinstalled when `requirements.txt` changes
- Runs the app as a non-root user (`appuser`)
- Serves the API with Gunicorn instead of the Django development server
- Serves static files with WhiteNoise

### docker-compose.yml

- `db`: PostgreSQL 17 with a health check and a volume for the data
- `backend`: built from the `Dockerfile`, starts only when the database is
  healthy, maps port `8000` and stores uploads in a volume
- Both services read their configuration from `.env`

The `.dockerignore` keeps the virtual environment, the database, `.env`
and cache files out of the image.

## Security

- No secrets in the code: `SECRET_KEY` and the database password come from
  `.env`, which is not in the repository
- Secure defaults: `DEBUG` is off by default and the app refuses to start
  without a `SECRET_KEY`
- Login and registration are limited to 5 requests per minute per client
  to slow down brute-force attacks (HTTP 429 when exceeded)
- Every endpoint requires authentication unless it is marked as public
- Object permissions make sure users can only change their own data
- The container runs as a non-root user
- Guest accounts are only created when `CREATE_GUEST_USERS=True`

## CI pipeline

GitHub Actions runs on every push and pull request
(`.github/workflows/ci.yml`):

| Job | What it does |
|---|---|
| Lint and tests | flake8, all tests on PostgreSQL, coverage of at least 95 % |
| Security scans | Bandit for the code, pip-audit for known vulnerabilities in the dependencies |
| Docker image scan | Builds the image and scans it with Trivy for critical and high vulnerabilities |

The Trivy action is pinned to a commit hash instead of a version tag, because
version tags can be changed afterwards.

## Tests

```bash
coverage run manage.py test
```

```bash
coverage report
```

## Code style

The code follows PEP 8. Check it with:

```bash
pip install flake8
```

```bash
flake8
```