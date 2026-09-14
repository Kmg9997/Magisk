FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.tgz.b64 /tmp/app.tgz.b64
RUN base64 -d /tmp/app.tgz.b64 > /tmp/app.tgz \
 && tar -xzf /tmp/app.tgz -C /app \
 && test -f /app/khalid_v070/app_cloud.py \
 && rm -f /tmp/app.tgz /tmp/app.tgz.b64

WORKDIR /app/khalid_v070
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["sh","-c","exec python -m uvicorn app_cloud:app --host 0.0.0.0 --port ${PORT:-8080}"]
