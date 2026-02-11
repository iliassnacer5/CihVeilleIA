FROM python:3.10-slim

WORKDIR /app

# Dépendances système pour FAISS et torch
RUN apt-get update && apt-get install -y \
    build-essential \
    libopenblas-dev \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Variables d'environnement par défaut
ENV MONGODB_URI=mongodb://mongo:27017/cih_veille
ENV PYTHONUNBUFFERED=1

EXPOSE 8501 8000

# Par défaut, on lance le dashboard
CMD ["streamlit", "run", "run_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
