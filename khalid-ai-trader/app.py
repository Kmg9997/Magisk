from __future__ import annotations

import math
import threading
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response

SYMBOL = "1320.SR"
NAME = "أنابيب السعودية — 1320"
CACHE_SECONDS = 45

app = FastAPI(title="Khalid AI Trader Live")
_lock = threading.Lock()
_cache = {"at": 0.0, "data": None}

def _now():
    return datetime.now(timezone.utc).isoformat()

def _fetch(interval: str, period: str) -> pd.DataFrame:
    df = yf.download(
        SYMBOL,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
        prepost=False,
    )
    if df is None or df.empty:
        raise RuntimeError(f"لم تصل بيانات {interval}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(c[0]).lower() for c in df.columns]
    else:
        df.columns = [str(c).lower() for c in df.columns]
    df = df.rename_axis("timestamp").reset_index()
    ts_col = "Datetime" if "Datetime" in df.columns else ("Date" if "Date" in df.columns else df.columns[0])
    df = df.rename(columns={ts_col: "timestamp"})
    df.columns = [str(c).strip().lower() for c in df.columns]
    need = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise RuntimeError("بيانات ناقصة: " + ",".join(missing))
    out = df[need].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce", utc=True)
    for c in ["open", "high", "low", "close", "volume"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.dropna().drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)

def _ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def _rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0)
    dn = -d.clip(upper=0)
    au = up.ewm(alpha=1/n, adjust=False).mean()
    ad = dn.ewm(alpha=1/n, adjust=False).mean()
    rs = au / (ad + 1e-12)
    return 100 - 100 / (1 + rs)

def _atr(df, n=14):
    pc = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - pc).abs(),
        (df["low"] - pc).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def _adx(df, n=14):
    up = df["high"].diff()
    dn = -df["low"].diff()
    plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    atr = _atr(df, n)
    plus_di = 100 * plus_dm.ewm(alpha=1/n, adjust=False).mean() / (atr + 1e-12)
    minus_di = 100 * minus_dm.ewm(alpha=1/n, adjust=False).mean() / (atr + 1e-12)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-12)
    adx = dx.ewm(alpha=1/n, adjust=False).mean()
    return adx, plus_di, minus_di

def _safe(x, digits=2):
    try:
        v = float(x)
        if not math.isfinite(v):
            return None
        return round(v, digits)
    except Exception:
        return None

def _analyze(df: pd.DataFrame, label: str) -> dict:
    if len(df) < 60:
        raise RuntimeError(f"بيانات {label} غير كافية")

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    vol = df["volume"].astype(float)

    e9 = _ema(close, 9)
    e21 = _ema(close, 21)
    e50 = _ema(close, 50)
    rsi = _rsi(close, 14)
    atr = _atr(df, 14)
    adx, pdi, mdi = _adx(df, 14)
    macd = _ema(close, 12) - _ema(close, 26)
    signal = _ema(macd, 9)
    hist = macd - signal

    typical = (high + low + close) / 3
    pv = typical * vol
    session = df["timestamp"].dt.date
    vwap = pv.groupby(session).cumsum() / (vol.groupby(session).cumsum() + 1e-12)

    mid = close.rolling(20).mean()
    std = close.rolling(20).std(ddof=0)
    bb_up = mid + 2 * std
    bb_dn = mid - 2 * std

    ll = low.rolling(14).min()
    hh = high.rolling(14).max()
    stoch = 100 * (close - ll) / (hh - ll + 1e-12)

    vol_avg = vol.rolling(20).mean()
    vol_ratio = vol / (vol_avg + 1e-12)

    last = -1
    price = float(close.iloc[last])
    score = 0.0
    reasons = []

    def add(points: float, txt: str):
        nonlocal score
        score += points
        reasons.append({"points": round(points, 1), "text": txt})

    if e9.iloc[last] > e21.iloc[last]:
        add(12, "EMA9 أعلى من EMA21")
    else:
        add(-12, "EMA9 أسفل EMA21")

    if e21.iloc[last] > e50.iloc[last]:
        add(10, "EMA21 أعلى من EMA50")
    else:
        add(-10, "EMA21 أسفل EMA50")

    if price > float(vwap.iloc[last]):
        add(8, "السعر فوق VWAP")
    else:
        add(-8, "السعر تحت VWAP")

    rv = float(rsi.iloc[last])
    if rv >= 55:
        add(8 if rv <= 72 else 2, f"RSI إيجابي {rv:.1f}")
    elif rv <= 45:
        add(-8 if rv >= 28 else -3, f"RSI ضعيف {rv:.1f}")
    else:
        add(0, f"RSI محايد {rv:.1f}")

    hv = float(hist.iloc[last])
    if hv > 0:
        add(8, "MACD histogram موجب")
    else:
        add(-8, "MACD histogram سالب")

    av = float(adx.iloc[last])
    if av >= 20:
        if float(pdi.iloc[last]) > float(mdi.iloc[last]):
            add(10, f"ADX {av:.1f} مع +DI أقوى")
        else:
            add(-10, f"ADX {av:.1f} مع -DI أقوى")
    else:
        add(0, f"ADX ضعيف {av:.1f}")

    vr = float(vol_ratio.iloc[last]) if math.isfinite(float(vol_ratio.iloc[last])) else 1.0
    if vr >= 1.2:
        add(5 if score >= 0 else -5, f"الحجم أعلى من المتوسط {vr:.2f}x")

    prev_high = float(high.iloc[-21:-1].max())
    prev_low = float(low.iloc[-21:-1].min())
    if price > prev_high:
        add(12, "اختراق أعلى 20 شمعة")
    elif price < prev_low:
        add(-12, "كسر أدنى 20 شمعة")

    o = float(df["open"].iloc[last])
    h = float(high.iloc[last])
    l = float(low.iloc[last])
    body = price - o
    rng = max(h - l, 1e-9)
    if body / rng > 0.45:
        add(4, "شمعة حالية شرائية")
    elif body / rng < -0.45:
        add(-4, "شمعة حالية بيعية")

    bb_pos = (price - float(bb_dn.iloc[last])) / (float(bb_up.iloc[last] - bb_dn.iloc[last]) + 1e-12)

    return {
        "label": label,
        "score": round(score, 2),
        "price": round(price, 2),
        "timestamp": str(df["timestamp"].iloc[last]),
        "rsi": _safe(rsi.iloc[last], 1),
        "adx": _safe(adx.iloc[last], 1),
        "plus_di": _safe(pdi.iloc[last], 1),
        "minus_di": _safe(mdi.iloc[last], 1),
        "ema9": _safe(e9.iloc[last], 2),
        "ema21": _safe(e21.iloc[last], 2),
        "ema50": _safe(e50.iloc[last], 2),
        "vwap": _safe(vwap.iloc[last], 2),
        "macd_hist": _safe(hist.iloc[last], 4),
        "atr_pct": _safe(100 * atr.iloc[last] / (price + 1e-12), 2),
        "volume_ratio": _safe(vr, 2),
        "stoch": _safe(stoch.iloc[last], 1),
        "bb_position": _safe(bb_pos, 2),
        "support": _safe(low.iloc[-40:].min(), 2),
        "resistance": _safe(high.iloc[-40:].max(), 2),
        "reasons": sorted(reasons, key=lambda x: abs(x["points"]), reverse=True)[:6],
    }

def _probabilities(score: float):
    edge = math.tanh(score / 35.0)
    mag = abs(edge)
    if score >= 0:
        p_up = 0.48 + 0.37 * mag
        p_down = 0.20 * (1 - mag)
    else:
        p_down = 0.48 + 0.37 * mag
        p_up = 0.20 * (1 - mag)
    p_wait = max(0.05, 1.0 - p_up - p_down)
    total = p_up + p_down + p_wait
    return p_up / total, p_down / total, p_wait / total

def _compute():
    d1 = _fetch("1m", "7d")
    d5 = _fetch("5m", "60d")
    d30 = _fetch("30m", "60d")

    a1 = _analyze(d1, "1 دقيقة")
    a5 = _analyze(d5, "5 دقائق")
    a30 = _analyze(d30, "30 دقيقة")

    combined = 0.25 * a1["score"] + 0.50 * a5["score"] + 0.25 * a30["score"]
    p_up, p_down, p_wait = _probabilities(combined)
    confidence = max(p_up, p_down, p_wait)

    if p_up >= 0.62 and combined >= 18:
        action = "إشارة صعود — تحتاج تأكيد تنفيذ"
    elif p_down >= 0.62 and combined <= -18:
        action = "إشارة هبوط / حذر"
    else:
        action = "انتظار"

    return {
        "symbol": SYMBOL,
        "name": NAME,
        "updated_at": _now(),
        "market_timestamp": a5["timestamp"],
        "price": a5["price"],
        "action": action,
        "score": round(combined, 2),
        "p_up": round(p_up * 100, 1),
        "p_down": round(p_down * 100, 1),
        "p_wait": round(p_wait * 100, 1),
        "confidence": round(confidence * 100, 1),
        "support": a5["support"],
        "resistance": a5["resistance"],
        "frames": {"1m": a1, "5m": a5, "30m": a30},
        "source": "Yahoo Finance — قد تكون البيانات متأخرة وليست بديلًا عن تنفيذات الوسيط اللحظية",
        "note": "النظام احتمالي وليس ضمانًا للصعود أو الهبوط. لا ينفذ صفقات تلقائيًا.",
    }

def _get_state(force=False):
    with _lock:
        age = time.time() - float(_cache["at"])
        if not force and _cache["data"] is not None and age < CACHE_SECONDS:
            return _cache["data"]
    data = _compute()
    with _lock:
        _cache["at"] = time.time()
        _cache["data"] = data
    return data

HTML = r"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b1020">
<title>Khalid AI Trader</title>
<style>
:root{--bg:#08101c;--card:#111b2b;--muted:#8ea0b8;--up:#20c77a;--dn:#ff5f6d;--wait:#f1b84b;--line:#22324a}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#07101c,#0c1422);color:#fff;font-family:Tahoma,Arial,sans-serif}
.wrap{max-width:760px;margin:auto;padding:18px 14px 38px}.top{display:flex;align-items:center;justify-content:space-between;gap:10px}
h1{font-size:22px;margin:0}.sub{color:var(--muted);font-size:13px;margin-top:5px}.pill{padding:7px 11px;border:1px solid var(--line);border-radius:999px;color:var(--muted)}
.card{background:rgba(17,27,43,.95);border:1px solid var(--line);border-radius:18px;padding:16px;margin-top:14px;box-shadow:0 12px 30px rgba(0,0,0,.18)}
.price{font-size:38px;font-weight:700}.action{font-size:20px;font-weight:700;margin-top:6px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:14px}
.box{background:#0c1524;border:1px solid var(--line);border-radius:14px;padding:12px;text-align:center}.box b{display:block;font-size:22px}.lbl{color:var(--muted);font-size:12px}
.up b{color:var(--up)}.dn b{color:var(--dn)}.wt b{color:var(--wait)}
.row{display:flex;justify-content:space-between;gap:14px;padding:10px 0;border-bottom:1px solid var(--line)}.row:last-child{border:0}
.frames{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.frame{background:#0c1524;border:1px solid var(--line);border-radius:13px;padding:10px}.frame strong{font-size:17px}
button{width:100%;border:0;border-radius:14px;padding:14px;margin-top:12px;background:#ff7a12;color:white;font-weight:700;font-size:16px}
small{color:var(--muted);line-height:1.6}.err{color:#ff9aa3}
@media(max-width:520px){.grid,.frames{grid-template-columns:1fr 1fr 1fr}.price{font-size:34px}}
</style>
</head>
<body><div class="wrap">
<div class="top"><div><h1>Khalid AI Trader</h1><div class="sub">أنابيب السعودية 1320</div></div><div class="pill" id="stamp">...</div></div>

<div class="card">
<div class="lbl">السعر من المصدر</div><div class="price" id="price">--</div>
<div class="action" id="action">جاري التحليل...</div>
<div class="grid">
<div class="box up"><span class="lbl">صعود</span><b id="up">--</b></div>
<div class="box wt"><span class="lbl">انتظار</span><b id="wait">--</b></div>
<div class="box dn"><span class="lbl">هبوط</span><b id="down">--</b></div>
</div>
</div>

<div class="card">
<div class="row"><span>درجة النموذج</span><b id="score">--</b></div>
<div class="row"><span>الثقة الأعلى</span><b id="conf">--</b></div>
<div class="row"><span>دعم قريب</span><b id="sup">--</b></div>
<div class="row"><span>مقاومة قريبة</span><b id="res">--</b></div>
</div>

<div class="card"><div class="lbl" style="margin-bottom:10px">الفواصل الزمنية</div><div class="frames">
<div class="frame"><span class="lbl">1 دقيقة</span><br><strong id="s1">--</strong><br><small id="r1">RSI --</small></div>
<div class="frame"><span class="lbl">5 دقائق</span><br><strong id="s5">--</strong><br><small id="r5">RSI --</small></div>
<div class="frame"><span class="lbl">30 دقيقة</span><br><strong id="s30">--</strong><br><small id="r30">RSI --</small></div>
</div>
<button onclick="load(true)">تحديث التحليل الآن</button></div>

<div class="card"><small id="note">البيانات البحثية قد تكون متأخرة. للمضاربة اللحظية قارن دائمًا مع دفتر الأوامر والتنفيذات في تطبيق الوسيط.</small><div class="err" id="err"></div></div>
</div>
<script>
async function load(force=false){
  document.getElementById('err').textContent='';
  try{
    const u=force?'/api/status?force=1':'/api/status';
    const r=await fetch(u,{cache:'no-store'}); if(!r.ok) throw new Error('HTTP '+r.status);
    const d=await r.json();
    price.textContent=(d.price??'--')+' ر.س';
    action.textContent=d.action||'--';
    up.textContent=d.p_up+'%'; down.textContent=d.p_down+'%'; wait.textContent=d.p_wait+'%';
    score.textContent=d.score; conf.textContent=d.confidence+'%';
    sup.textContent=d.support??'--'; res.textContent=d.resistance??'--';
    s1.textContent=d.frames['1m'].score; r1.textContent='RSI '+d.frames['1m'].rsi+' | ADX '+d.frames['1m'].adx;
    s5.textContent=d.frames['5m'].score; r5.textContent='RSI '+d.frames['5m'].rsi+' | ADX '+d.frames['5m'].adx;
    s30.textContent=d.frames['30m'].score; r30.textContent='RSI '+d.frames['30m'].rsi+' | ADX '+d.frames['30m'].adx;
    stamp.textContent='آخر تحديث '+new Date(d.updated_at).toLocaleTimeString('ar-SA',{hour:'2-digit',minute:'2-digit'});
    note.textContent=d.source+' — '+d.note;
  }catch(e){document.getElementById('err').textContent='تعذر التحديث: '+e.message}
}
load(); setInterval(()=>load(false),60000);
</script></body></html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(HTML)

@app.get("/health")
def health():
    return {"ok": True, "service": "khalid-ai-trader-live", "symbol": SYMBOL}

@app.get("/api/status")
def status(force: int = 0):
    try:
        return JSONResponse(_get_state(bool(force)), headers={"Cache-Control":"no-store"})
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "updated_at": _now(),
            "symbol": SYMBOL,
            "name": NAME,
            "note": "تعذر جلب بيانات السوق مؤقتًا"
        }, status_code=503, headers={"Cache-Control":"no-store"})

@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse({
        "name":"Khalid AI Trader",
        "short_name":"Khalid Trader",
        "start_url":"/",
        "display":"standalone",
        "background_color":"#08101c",
        "theme_color":"#08101c"
    }, media_type="application/manifest+json")

@app.get("/service-worker.js")
def sw():
    return Response("self.addEventListener('fetch',()=>{});", media_type="application/javascript")
