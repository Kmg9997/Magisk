FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.part*.b64 /tmp/
RUN cat /tmp/app.part*.b64 | base64 -d > /tmp/app.tgz \
 && tar -xzf /tmp/app.tgz -C /app \
 && test -f /app/khalid_v100/app_cloud.py \
 && rm -f /tmp/app.tgz /tmp/app.part*.b64

WORKDIR /app/khalid_v100
# DIAG_MARKET_CONTEXT
RUN python - <<'PY'
from pathlib import Path
p=Path('app_cloud.py')
lines=p.read_text(encoding='utf-8').splitlines()
print('=== FETCH_BLOCK ===')
for j in range(97,145):
    if j < len(lines): print(f'{j+1:04d}: {lines[j]}')
print('=== MARKET_CONTEXT_HITS ===')
for i,line in enumerate(lines):
    if any(k in line for k in ['market_close','sector_close','^TASI','merge(','concat(']):
        print(f'--- app_cloud.py:{i+1} ---')
        for j in range(max(0,i-4), min(len(lines),i+5)):
            print(f'{j+1:04d}: {lines[j]}')
PY

# DIAG_TO_NUMERIC: print source context during build; does not change runtime behavior.
RUN python - <<'PY'
from pathlib import Path
for p in Path('.').rglob('*.py'):
    try:
        lines=p.read_text(encoding='utf-8').splitlines()
    except Exception:
        continue
    for i,line in enumerate(lines):
        if 'to_numeric' in line or 'yf.download' in line or 'yfinance' in line:
            print(f'=== {p}:{i+1} ===')
            for j in range(max(0,i-5), min(len(lines),i+6)):
                print(f'{j+1:04d}: {lines[j]}')
PY
RUN python -c 'from pathlib import Path; import base64; p=Path("static/index.html"); s=p.read_text(encoding="utf-8"); old=base64.b64decode("IGlmKGxhc3RBY3Rpb24gJiYgbGFzdEFjdGlvbiE9PWQuYWN0aW9uICYmIE5vdGlmaWNhdGlvbj8ucGVybWlzc2lvbj09PSdncmFudGVkJyl7bmV3IE5vdGlmaWNhdGlvbignS2hhbGlkIEFJIFRyYWRlcicse2JvZHk6YNiq2LrZitix2Kog2KfZhNil2LTYp9ix2Kk6ICR7ZC5hY3Rpb259IHwgJHtkLnByaWNlPz8n4oCUJ30g2LEu2LNgLGljb246Jy9pY29uLnN2Zyd9KTt9IGxhc3RBY3Rpb249ZC5hY3Rpb247").decode(); new=base64.b64decode("IGlmKGxhc3RBY3Rpb24gJiYgbGFzdEFjdGlvbiE9PWQuYWN0aW9uICYmICdOb3RpZmljYXRpb24nIGluIHdpbmRvdyAmJiBOb3RpZmljYXRpb24ucGVybWlzc2lvbj09PSdncmFudGVkJyAmJiAnc2VydmljZVdvcmtlcicgaW4gbmF2aWdhdG9yKXtuYXZpZ2F0b3Iuc2VydmljZVdvcmtlci5yZWFkeS50aGVuKHJlZz0+cmVnLnNob3dOb3RpZmljYXRpb24oJ0toYWxpZCBBSSBUcmFkZXInLHtib2R5OmDYqti62YrYsdiqINin2YTYpdi02KfYsdipOiAke2QuYWN0aW9ufSB8ICR7ZC5wcmljZT8/J+KAlCd9INixLtizYCxpY29uOicvaWNvbi5zdmcnLGJhZGdlOicvaWNvbi5zdmcnLHRhZzona2hhbGlkLWFpLXNpZ25hbCcscmVub3RpZnk6dHJ1ZSxkYXRhOnt1cmw6Jy8nfX0pKS5jYXRjaChlcnI9PmNvbnNvbGUud2FybignTm90aWZpY2F0aW9uIGZhaWxlZCcsZXJyKSk7fSBsYXN0QWN0aW9uPWQuYWN0aW9uOw==").decode(); assert old in s or "new Notification" not in s, "unexpected notification code"; s=s.replace(old,new); p.write_text(s,encoding="utf-8"); sw=Path("static/service-worker.js"); t=sw.read_text(encoding="utf-8"); t=t.replace("khalid-ai-v090-shell","khalid-ai-v101-shell").replace("khalid-ai-v100-shell","khalid-ai-v101-shell"); click=base64.b64decode("CnNlbGYuYWRkRXZlbnRMaXN0ZW5lcignbm90aWZpY2F0aW9uY2xpY2snLGV2ZW50PT57ZXZlbnQubm90aWZpY2F0aW9uLmNsb3NlKCk7Y29uc3QgdXJsPWV2ZW50Lm5vdGlmaWNhdGlvbj8uZGF0YT8udXJsfHwnLyc7ZXZlbnQud2FpdFVudGlsKGNsaWVudHMubWF0Y2hBbGwoe3R5cGU6J3dpbmRvdycsaW5jbHVkZVVuY29udHJvbGxlZDp0cnVlfSkudGhlbihsaXN0PT57Zm9yKGNvbnN0IGNsaWVudCBvZiBsaXN0KXtpZignZm9jdXMnIGluIGNsaWVudCl7Y2xpZW50Lm5hdmlnYXRlKHVybCk7cmV0dXJuIGNsaWVudC5mb2N1cygpO319cmV0dXJuIGNsaWVudHMub3BlbldpbmRvdz9jbGllbnRzLm9wZW5XaW5kb3codXJsKTp1bmRlZmluZWQ7fSkpO30pOwo=").decode(); sw.write_text(t+(click if "notificationclick" not in t else ""),encoding="utf-8")'
RUN sed -i 's/^xgboost.*$/xgboost-cpu==3.4.1/' requirements.txt \
 && pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    MALLOC_ARENA_MAX=2

EXPOSE 10000
CMD ["sh","-c","exec python -m uvicorn app_cloud:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
