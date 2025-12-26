FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY html/ /app/frontend_html/

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "payevo_proxy.wsgi", "--bind", "0.0.0.0:8000", "--workers", "4"]
