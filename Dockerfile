FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser \
    && mkdir -p /app/media /app/staticfiles \
    && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && if [ \"$CREATE_GUEST_USERS\" = \"True\" ]; then python manage.py create_guest_users; fi && gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
