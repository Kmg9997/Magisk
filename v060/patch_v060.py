from pathlib import Path

root = Path("/appsrc/khalid_ai_trader_v040_mobile_cloud")
app = root / "app_cloud.py"
idx = root / "static" / "index.html"

s = app.read_text(encoding="utf-8")

channel_func = r'''

def price_channel(df: pd.DataFrame, max_bars: int = 60) -> dict[str, Any]:
    """Dynamic linear-regression channel fitted to completed prior 5m bars.

    The current bar is evaluated against a channel fitted to previous bars, so
    a fresh breakout does not move the boundary away from price.
    """
    empty = {
        "direction": "غير متاح", "status": "بيانات غير كافية",
        "upper": None, "mid": None, "lower": None, "position": None,
        "slope_pct_per_bar": None, "slope_atr": None, "atr": None,
        "volume_ratio": None, "take_profit": None, "invalidation": None,
        "breakout_confirm": None, "breakdown_confirm": None,
        "breakout": False, "breakdown": False, "window": 0,
    }
    if df is None or len(df) < 24:
        return empty

    hist_n = min(max_bars, len(df) - 1)
    hist = df.iloc[-(hist_n + 1):-1].copy()
    cur = df.iloc[-1]
    if len(hist) < 20:
        return empty

    x = np.arange(len(hist), dtype=float)
    typical = ((hist["high"] + hist["low"] + hist["close"]) / 3.0).astype(float).to_numpy()
    slope, intercept = np.polyfit(x, typical, 1)
    mid_hist = slope * x + intercept
    mid_now = float(slope * len(hist) + intercept)

    high_gap = np.asarray(hist["high"], dtype=float) - mid_hist
    low_gap = mid_hist - np.asarray(hist["low"], dtype=float)

    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = float(tr.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1])
    price = float(cur["close"])
    if not np.isfinite(atr) or atr <= 0:
        atr = max(price * 0.003, 0.01)

    upper_gap = max(float(np.nanpercentile(high_gap, 90)), 0.60 * atr)
    lower_gap = max(float(np.nanpercentile(low_gap, 90)), 0.60 * atr)
    upper = mid_now + upper_gap
    lower = mid_now - lower_gap
    width = max(upper - lower, 1e-9)
    position = (price - lower) / width
    slope_atr = slope / (atr + 1e-12)
    slope_pct = slope / (price + 1e-12) * 100.0

    if slope_atr > 0.025:
        direction = "صاعدة"
    elif slope_atr < -0.025:
        direction = "هابطة"
    else:
        direction = "عرضية"

    vol_mean = float(df["volume"].iloc[-21:-1].mean()) if len(df) >= 21 else float(hist["volume"].mean())
    vol_ratio = float(cur["volume"]) / (vol_mean + 1e-12) if vol_mean > 0 else 1.0
    buffer = max(0.12 * atr, 0.00035 * price)

    breakout = bool(price > upper + buffer and vol_ratio >= 1.15)
    breakdown = bool(price < lower - buffer and vol_ratio >= 1.15)

    if breakout:
        status = "اختراق علوي مؤكد نسبيًا بالحجم"
    elif breakdown:
        status = "كسر سفلي مؤكد نسبيًا بالحجم"
    elif position >= 0.82:
        status = "قرب الحد العلوي / منطقة مقاومة"
    elif position <= 0.18:
        status = "قرب الحد السفلي / منطقة دعم"
    else:
        status = "داخل القناة"

    take_profit = upper if not breakout else upper + 0.35 * width
    invalidation = lower - buffer

    return {
        "direction": direction,
        "status": status,
        "upper": round(upper, 2),
        "mid": round(mid_now, 2),
        "lower": round(lower, 2),
        "position": round(float(position), 4),
        "slope_pct_per_bar": round(float(slope_pct), 4),
        "slope_atr": round(float(slope_atr), 4),
        "atr": round(float(atr), 4),
        "volume_ratio": round(float(vol_ratio), 2),
        "take_profit": round(float(take_profit), 2),
        "invalidation": round(float(invalidation), 2),
        "breakout_confirm": round(float(upper + buffer), 2),
        "breakdown_confirm": round(float(lower - buffer), 2),
        "breakout": breakout,
        "breakdown": breakdown,
        "window": int(len(hist)),
    }
'''

needle = "\n@dataclass\nclass RuntimeState:"
if needle not in s:
    raise RuntimeError("RuntimeState marker not found")
s = s.replace(needle, channel_func + needle, 1)

s = s.replace(
    '    resistance: float | None = None\n    contexts: dict[str, Any] = field(default_factory=dict)\n',
    '    resistance: float | None = None\n    channel: dict[str, Any] = field(default_factory=dict)\n    contexts: dict[str, Any] = field(default_factory=dict)\n',
    1
)

s = s.replace(
    '        lv = levels(df5)\n        c1 = simple_context(df1)\n',
    '        lv = levels(df5)\n        ch = price_channel(df5)\n        c1 = simple_context(df1)\n',
    1
)

s = s.replace(
    '        price = float(df5.iloc[-1]["close"])\n        market_ts = str(df5.iloc[-1]["timestamp"])\n',
    '        # Display the freshest 1-minute price available from the current source.\n        price = float(df1.iloc[-1]["close"])\n        market_ts = str(df1.iloc[-1]["timestamp"])\n',
    1
)

old_block = '''                STATE.support = lv["support"]
                STATE.resistance = lv["resistance"]
                STATE.contexts = {"1m": c1, "5m": c5, "30m": c30}
'''
new_block = '''                STATE.support = lv["support"]
                STATE.resistance = lv["resistance"]
                STATE.channel = ch
                STATE.contexts = {"1m": c1, "5m": c5, "30m": c30}
'''
if old_block not in s:
    raise RuntimeError("First state block not found")
s = s.replace(old_block, new_block, 1)

old_dec = '''        qualified = bool(STATE.qualified)
        action = dec["action"]
        if not qualified:
            action = "انتظار — النموذج غير مؤهل ماليًا"

        with LOCK:
'''
new_dec = '''        qualified = bool(STATE.qualified)
        action = dec["action"]

        # Conservative gate: the channel can veto a long signal, but it never
        # creates a buy signal by itself.
        channel_reason = f"القناة {ch.get('direction', 'غير متاح')}: {ch.get('status', '')}"
        if ch.get("breakdown"):
            action = "تحذير هابط / كسر القناة"
            channel_reason += f" — كسر تحت {ch.get('breakdown_confirm')}"
        elif "ميل صاعد" in action and ch.get("direction") == "هابطة" and not ch.get("breakout"):
            action = "انتظار — القناة لا تؤكد الصعود"
        elif ch.get("breakout"):
            channel_reason += f" — اختراق فوق {ch.get('breakout_confirm')}"

        if not qualified:
            action = "انتظار — النموذج غير مؤهل ماليًا"

        with LOCK:
'''
if old_dec not in s:
    raise RuntimeError("Decision block not found")
s = s.replace(old_dec, new_dec, 1)

old_final = '''            STATE.support = lv["support"]
            STATE.resistance = lv["resistance"]
            STATE.contexts = {"1m": c1, "5m": c5, "30m": c30}
            STATE.reasons = list(dec["reasons"])
'''
new_final = '''            STATE.support = lv["support"]
            STATE.resistance = lv["resistance"]
            STATE.channel = ch
            STATE.contexts = {"1m": c1, "5m": c5, "30m": c30}
            STATE.reasons = [channel_reason] + list(dec["reasons"])
'''
if old_final not in s:
    raise RuntimeError("Final state block not found")
s = s.replace(old_final, new_final, 1)

s = s.replace(
    'FastAPI(title="Khalid AI Trader Mobile Cloud v0.5")',
    'FastAPI(title="Khalid AI Trader Mobile Cloud v0.6")'
)
app.write_text(s, encoding="utf-8")

h = idx.read_text(encoding="utf-8")
h = h.replace("Mobile Cloud v0.5", "Mobile Cloud v0.6")

css_marker = '.reason{padding:10px 0;border-bottom:1px solid var(--line);font-size:14px}.reason:last-child{border:0}.warning'
css_insert = '.channelGrid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.channelStatus{margin-top:10px;padding:10px 12px;border-radius:12px;background:#0b1528;border:1px solid var(--line);font-size:13px;line-height:1.6}.channelTrack{position:relative;height:16px;border-radius:999px;background:linear-gradient(90deg,#12223a,#1e3856);border:1px solid var(--line);margin-top:12px;overflow:visible}.channelMarker{position:absolute;top:50%;width:16px;height:16px;border-radius:50%;background:#e5f1ff;border:3px solid #2563eb;transform:translate(-50%,-50%);box-shadow:0 0 12px #2563ebaa}.channelLabels{display:flex;justify-content:space-between;color:var(--muted);font-size:11px;margin-top:6px}.techNote{font-size:11px;color:#9fb1c9;line-height:1.6;margin-top:10px}.reason{padding:10px 0;border-bottom:1px solid var(--line);font-size:14px}.reason:last-child{border:0}.warning'
if css_marker not in h:
    raise RuntimeError("CSS marker not found")
h = h.replace(css_marker, css_insert, 1)

section_marker = '  <section class="section"><div class="title">الاتجاه متعدد الفواصل</div>'
channel_section = '''  <section class="section">
    <div class="title">القناة السعرية الديناميكية</div>
    <div class="channelGrid">
      <div class="mini"><div class="lab">اتجاه القناة</div><div class="val" id="chDirection">—</div></div>
      <div class="mini"><div class="lab">حالة السعر</div><div class="val" style="font-size:13px" id="chStatus">—</div></div>
      <div class="mini"><div class="lab">الحد العلوي</div><div class="val" id="chUpper">—</div></div>
      <div class="mini"><div class="lab">منتصف القناة</div><div class="val" id="chMid">—</div></div>
      <div class="mini"><div class="lab">الحد السفلي</div><div class="val" id="chLower">—</div></div>
      <div class="mini"><div class="lab">ميل القناة / شمعة</div><div class="val" id="chSlope">—</div></div>
      <div class="mini"><div class="lab">منطقة جني/مقاومة فنية</div><div class="val" id="chTake">—</div></div>
      <div class="mini"><div class="lab">إبطال السيناريو الفني</div><div class="val" id="chStop">—</div></div>
    </div>
    <div class="channelTrack"><div id="chMarker" class="channelMarker" style="left:50%"></div></div>
    <div class="channelLabels"><span id="chLowLabel">سفلي —</span><span id="chPosLabel">الموقع —</span><span id="chHighLabel">علوي —</span></div>
    <div class="channelStatus" id="chConfirm">بانتظار بيانات القناة…</div>
    <div class="techNote">المستويات فنية فقط. القناة فلتر إضافي ولا تصدر إشارة شراء وحدها.</div>
  </section>

'''
if section_marker not in h:
    raise RuntimeError("Section marker not found")
h = h.replace(section_marker, channel_section + section_marker, 1)

js_marker = "async function getStatus(){const r=await fetch('/api/status',{cache:'no-store'});"
render_channel = r'''function renderChannel(c){
 c=c||{};
 $('chDirection').textContent=c.direction||'—';
 $('chDirection').className='val '+(c.direction==='صاعدة'?'up':c.direction==='هابطة'?'down':'neutral');
 $('chStatus').textContent=c.status||'—';
 $('chUpper').textContent=c.upper??'—'; $('chMid').textContent=c.mid??'—'; $('chLower').textContent=c.lower??'—';
 $('chSlope').textContent=c.slope_pct_per_bar==null?'—':Number(c.slope_pct_per_bar).toFixed(3)+'%';
 $('chTake').textContent=c.take_profit??'—'; $('chStop').textContent=c.invalidation??'—';
 $('chLowLabel').textContent='سفلي '+(c.lower??'—'); $('chHighLabel').textContent='علوي '+(c.upper??'—');
 const raw=c.position==null?0.5:Number(c.position), pos=Math.max(0,Math.min(1,raw));
 $('chMarker').style.left=(pos*100).toFixed(1)+'%'; $('chPosLabel').textContent='موقع السعر '+(raw*100).toFixed(0)+'%';
 let msg='داخل القناة';
 if(c.breakout) msg='✅ اختراق علوي مؤكد نسبيًا بالحجم فوق '+(c.breakout_confirm??'—');
 else if(c.breakdown) msg='⚠️ كسر سفلي مؤكد نسبيًا بالحجم تحت '+(c.breakdown_confirm??'—');
 else if(c.status) msg=c.status+' | حجم '+(c.volume_ratio??'—')+'× | نافذة '+(c.window??'—')+' شمعة';
 $('chConfirm').textContent=msg;
}
'''
if js_marker not in h:
    raise RuntimeError("JS marker not found")
h = h.replace(js_marker, render_channel + js_marker, 1)

render_marker = " setTrend('t1','r1',d.contexts?.['1m']);"
if render_marker not in h:
    raise RuntimeError("Render marker not found")
h = h.replace(render_marker, " renderChannel(d.channel);" + render_marker, 1)

idx.write_text(h, encoding="utf-8")
print("v0.6 patch applied")
