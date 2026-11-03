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

# Stabilize Yahoo single-symbol downloads and normalize duplicated columns safely.
RUN python - <<'PY'
from pathlib import Path
p = Path("app_cloud.py")
s = p.read_text(encoding="utf-8")

marker = 'MODEL_VERSION = "1.0 Pro"\n'
if "YF_DOWNLOAD_LOCK" not in s:
    assert marker in s, "model version marker not found"
    s = s.replace(marker, marker + '\nYF_DOWNLOAD_LOCK = threading.Lock()\n', 1)

old_cols = '''    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={"datetime": "timestamp", "date": "timestamp"})
'''
new_cols = '''    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()
    df = df.rename(columns={"datetime": "timestamp", "date": "timestamp"})
'''
if old_cols in s:
    s = s.replace(old_cols, new_cols, 1)

old_numeric = '''    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
'''
new_numeric = '''    for c in ["open", "high", "low", "close", "volume"]:
        col = df[c]
        if isinstance(col, pd.DataFrame):
            col = col.iloc[:, 0]
        df[c] = pd.to_numeric(col, errors="coerce")
'''
if old_numeric in s:
    s = s.replace(old_numeric, new_numeric, 1)

old_fetch = '''    raw = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
        prepost=False,
    )
'''
new_fetch = '''    with YF_DOWNLOAD_LOCK:
        raw = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
            prepost=False,
        )
'''
if old_fetch in s:
    s = s.replace(old_fetch, new_fetch, 1)

assert "with YF_DOWNLOAD_LOCK:" in s, "Yahoo lock patch not applied"
assert "df.columns.duplicated().any()" in s, "duplicate-column guard not applied"
assert "if isinstance(col, pd.DataFrame):" in s, "1-D numeric guard not applied"
p.write_text(s, encoding="utf-8")
PY

# Android/PWA notifications must go through the service worker.
RUN python -c 'from pathlib import Path; import base64; p=Path("static/index.html"); s=p.read_text(encoding="utf-8"); old=base64.b64decode("IGlmKGxhc3RBY3Rpb24gJiYgbGFzdEFjdGlvbiE9PWQuYWN0aW9uICYmIE5vdGlmaWNhdGlvbj8ucGVybWlzc2lvbj09PSdncmFudGVkJyl7bmV3IE5vdGlmaWNhdGlvbignS2hhbGlkIEFJIFRyYWRlcicse2JvZHk6YNiq2LrZitix2Kog2KfZhNil2LTYp9ix2Kk6ICR7ZC5hY3Rpb259IHwgJHtkLnByaWNlPz8n4oCUJ30g2LEu2LNgLGljb246Jy9pY29uLnN2Zyd9KTt9IGxhc3RBY3Rpb249ZC5hY3Rpb247").decode(); new=base64.b64decode("IGlmKGxhc3RBY3Rpb24gJiYgbGFzdEFjdGlvbiE9PWQuYWN0aW9uICYmICdOb3RpZmljYXRpb24nIGluIHdpbmRvdyAmJiBOb3RpZmljYXRpb24ucGVybWlzc2lvbj09PSdncmFudGVkJyAmJiAnc2VydmljZVdvcmtlcicgaW4gbmF2aWdhdG9yKXtuYXZpZ2F0b3Iuc2VydmljZVdvcmtlci5yZWFkeS50aGVuKHJlZz0+cmVnLnNob3dOb3RpZmljYXRpb24oJ0toYWxpZCBBSSBUcmFkZXInLHtib2R5OmDYqti62YrYsdiqINin2YTYpdi02KfYsdipOiAke2QuYWN0aW9ufSB8ICR7ZC5wcmljZT8/J+KAlCd9INixLtizYCxpY29uOicvaWNvbi5zdmcnLGJhZGdlOicvaWNvbi5zdmcnLHRhZzona2hhbGlkLWFpLXNpZ25hbCcscmVub3RpZnk6dHJ1ZSxkYXRhOnt1cmw6Jy8nfX0pKS5jYXRjaChlcnI9PmNvbnNvbGUud2FybignTm90aWZpY2F0aW9uIGZhaWxlZCcsZXJyKSk7fSBsYXN0QWN0aW9uPWQuYWN0aW9uOw==").decode(); assert old in s or "new Notification" not in s, "unexpected notification code"; s=s.replace(old,new); p.write_text(s,encoding="utf-8"); sw=Path("static/service-worker.js"); t=sw.read_text(encoding="utf-8"); t=t.replace("khalid-ai-v090-shell","khalid-ai-v102-shell").replace("khalid-ai-v100-shell","khalid-ai-v102-shell").replace("khalid-ai-v101-shell","khalid-ai-v102-shell"); click=base64.b64decode("CnNlbGYuYWRkRXZlbnRMaXN0ZW5lcignbm90aWZpY2F0aW9uY2xpY2snLGV2ZW50PT57ZXZlbnQubm90aWZpY2F0aW9uLmNsb3NlKCk7Y29uc3QgdXJsPWV2ZW50Lm5vdGlmaWNhdGlvbj8uZGF0YT8udXJsfHwnLyc7ZXZlbnQud2FpdFVudGlsKGNsaWVudHMubWF0Y2hBbGwoe3R5cGU6J3dpbmRvdycsaW5jbHVkZVVuY29udHJvbGxlZDp0cnVlfSkudGhlbihsaXN0PT57Zm9yKGNvbnN0IGNsaWVudCBvZiBsaXN0KXtpZignZm9jdXMnIGluIGNsaWVudCl7Y2xpZW50Lm5hdmlnYXRlKHVybCk7cmV0dXJuIGNsaWVudC5mb2N1cygpO319cmV0dXJuIGNsaWVudHMub3BlbldpbmRvdz9jbGllbnRzLm9wZW5XaW5kb3codXJsKTp1bmRlZmluZWQ7fSkpO30pOwo=").decode(); sw.write_text(t+(click if "notificationclick" not in t else ""),encoding="utf-8")'

RUN sed -i 's/^xgboost.*$/xgboost-cpu==3.4.1/' requirements.txt \
 && pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    MALLOC_ARENA_MAX=2

EXPOSE 8080
CMD ["sh","-c","exec python -m uvicorn app_cloud:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
