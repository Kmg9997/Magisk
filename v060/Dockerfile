FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /work
COPY v050_1.b64 v050_2.b64 patch_v060.py ./
RUN cat v050_1.b64 v050_2.b64 | base64 -d > app.tgz \
    && mkdir -p /appsrc \
    && tar -xzf app.tgz -C /appsrc \
    && python patch_v060.py \
    && cd /appsrc/khalid_ai_trader_v040_mobile_cloud \
    && python -m py_compile app_cloud.py \
    && pip install --no-cache-dir -r requirements.txt
WORKDIR /appsrc/khalid_ai_trader_v040_mobile_cloud
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["sh","-c","exec uvicorn app_cloud:app --host 0.0.0.0 --port ${PORT:-8080}"]
