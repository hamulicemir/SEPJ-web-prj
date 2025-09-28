FROM python:3.11-slim
ENV HF_HOME=/data/hf_cache
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
# Torch CPU zuerst (stabil in Containern auf Windows)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 9000
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","9000"]
