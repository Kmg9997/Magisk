FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY khalid-ai-trader-full/part1.b64 /tmp/part1.b64
COPY khalid-ai-trader-full/part2.b64 /tmp/part2.b64

RUN cat /tmp/part1.b64 /tmp/part2.b64 | base64 -d > /tmp/app.tgz \
    && mkdir -p /appsrc \
    && tar -xzf /tmp/app.tgz -C /appsrc \
    && test -f /appsrc/khalid_ai_trader_v040_mobile_cloud/app_cloud.py \
    && rm -f /tmp/app.tgz /tmp/part1.b64 /tmp/part2.b64

WORKDIR /appsrc/khalid_ai_trader_v040_mobile_cloud
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["sh","-c","exec uvicorn app_cloud:app --host 0.0.0.0 --port ${PORT:-8080}"]
