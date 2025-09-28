FROM python:3.11-slim

# Schnellere Starts bei Folgeläufen
ENV HF_HOME=/data/hf_cache

# Basis-Tools (git optional, aber praktisch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Erst Torch (CPU) installieren, dann Rest – macht Builds stabiler
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Deine App
COPY main.py .

# Standard-Env (kannst du beim Run überschreiben)
ENV MODEL_ID=google/gemma-2-2b-it

CMD ["python", "main.py"]