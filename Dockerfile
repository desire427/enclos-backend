FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Télécharger le modèle depuis Hugging Face
RUN mkdir -p /models && \
    curl -L -o /models/model_soutenance_simplon.joblib \
    https://huggingface.co/D4rkN3st/model_soutenance_simplon/resolve/main/model_soutenance_simplon.joblib

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]