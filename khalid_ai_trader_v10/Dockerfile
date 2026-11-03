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
# DIAG_NORMALIZE_YF
RUN python - <<'PY'
from pathlib import Path
lines=Path('app_cloud.py').read_text(encoding='utf-8').splitlines()
print('=== NORMALIZE_YF_BLOCK ===')
for j in range(55,98):
    if j < len(lines): print(f'{j+1:04d}: {lines[j]}')
PY

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
# DIAG_REFRESH_FLOW
RUN python - <<'PY'
from pathlib import Path
lines=Path('app_cloud.py').read_text(encoding='utf-8').splitlines()
print('=== REFRESH_FLOW_HITS ===')
for i,line in enumerate(lines):
    if any(k in line for k in ['/api/refresh','def refresh','def update','attach_market_context(','prepare_dataframe','normalize_market','build_features','train_']):
        print(f'--- app_cloud.py:{i+1} ---')
        for j in range(max(0,i-7), min(len(lines),i+18)):
            print(f'{j+1:04d}: {lines[j]}')
PY

# DIAG_YAHOO_1820
RUN python - <<'PY'
import yfinance as yf
for sym in ['1820.SR','^TASI.SR']:
    try:
        raw=yf.download(sym,period='5d',interval='5m',auto_adjust=False,progress=False,threads=False,prepost=False)
        print('=== YF_RAW',sym,'===')
        print('columns_type=',type(raw.columns).__name__)
        print('columns=',repr(list(raw.columns)))
        print('shape=',raw.shape)
    except Exception as e:
        print('=== YF_RAW_ERROR',sym,repr(e))
PY

# DIAG_PIPELINE_1820
RUN python - <<'PY'
import traceback
import app_cloud as a
try:
    df5=a.fetch('1820.SR','5m','60d'); print('STEP fetch5 OK',df5.shape)
    df1=a.fetch('1820.SR','1m','7d'); print('STEP fetch1 OK',df1.shape)
    m=a.fetch(a.MARKET_SYMBOL,'5m','60d'); print('STEP market OK',m.shape)
    df5=a.attach_market_context(df5,m); print('STEP attach OK',df5.shape, list(df5.columns))
    df30=a.resample_ohlcv(df5,30); print('STEP r30 OK',df30.shape)
    df60=a.resample_ohlcv(df5,60); print('STEP r60 OK',df60.shape)
    lv=a.levels(df5); print('STEP levels OK')
    ch=a.price_channel(df5,lookback=120); print('STEP ch5 OK')
    ch30=a.price_channel(df30,lookback=96); print('STEP ch30 OK')
    ch60=a.price_channel(df60,lookback=80); print('STEP ch60 OK')
    st=a.structure_consensus(ch,ch30,ch60); print('STEP structure OK')
    dq=a.assess_data_quality(df5); print('STEP dq OK')
    c1=a.simple_context(df1); print('STEP c1 OK')
    c5=a.simple_context(df5); print('STEP c5 OK')
    c30=a.simple_context(df30); print('STEP c30 OK')
    c60=a.simple_context(df60); print('STEP c60 OK')
except Exception as e:
    print('PIPELINE_FAIL',type(e).__name__,repr(e))
    traceback.print_exc()
PY

ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    MALLOC_ARENA_MAX=2

EXPOSE 10000
CMD ["sh","-c","exec python -m uvicorn app_cloud:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
