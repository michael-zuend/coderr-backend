# Coderr Backend

REST API for **Coderr**, a freelancer platform where business users offer
services and customers order and review them. Built with Django and
Django REST Framework.

The frontend is not part of this repository.

## Tech stack

- Python 3.12+
- Django 6.1
- Django REST Framework (token authentication)
- SQLite (development database)

## Setup

```bash
git clone https://github.com/michael-zuend/coderr-backend.git
cd coderr-backend
python -m venv env
env\Scripts\activate          # Windows
source env/bin/activate       # macOS/Linux
pip install -r requirements.txt
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
python manage.py migrate
python manage.py create_guest_users
python manage.py createsuperuser
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

By default the frontend is expected at `http://127.0.0.1:5500`
(VS Code Live Server).

### Guest accounts

`python manage.py create_guest_users` creates the guest accounts used by the
guest login of the frontend:

| Username | Password | Type |
|---|---|---|
| `andrey` | `asdasd` | customer |
| `kevin` | `asdasd24` | business |

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

## Tests

```bash
coverage run manage.py test
coverage report
```

## Code style

The code follows PEP 8. Check it with:

```bash
pip install flake8
flake8
```
