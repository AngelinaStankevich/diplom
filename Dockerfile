FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false

COPY . .

RUN poetry install --only main

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "finance_manager.wsgi:application", "--bind", "0.0.0.0:8000"]
