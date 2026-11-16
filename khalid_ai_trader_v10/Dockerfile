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

# Dynamic channel labels on the chart: blue = resistance, green = support.
RUN python - <<'PY'
from pathlib import Path
p=Path("static/index.html")
s=p.read_text(encoding="utf-8")
old="""    const mkLine=(key,color,width=2,style=LC.LineStyle?.Dashed ?? 2)=>{
      const ser=chart.addSeries(LC.LineSeries,{color,lineWidth:width,lineStyle:style,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});
      const data=sr.filter(x=>x[key]!=null&&isFinite(+x[key])).map(x=>({time:Math.floor(new Date(x.timestamp).getTime()/1000),value:+x[key]}));
      if(data.length>1)ser.setData(data);
      return ser;
    };
    if(sr.length>1){mkLine('upper','#38bdf8',2);mkLine('middle','#a78bfa',1,LC.LineStyle?.Solid ?? 0);mkLine('lower','#2dd4bf',2);}
"""
new="""    const mkLine=(key,color,width=2,style=LC.LineStyle?.Dashed ?? 2,label='')=>{
      const ser=chart.addSeries(LC.LineSeries,{color,lineWidth:width,lineStyle:style,priceLineVisible:false,lastValueVisible:false,crosshairMarkerVisible:false});
      const data=sr.filter(x=>x[key]!=null&&isFinite(+x[key])).map(x=>({time:Math.floor(new Date(x.timestamp).getTime()/1000),value:+x[key]}));
      if(data.length>1){
        ser.setData(data);
        if(label && typeof ser.createPriceLine==='function'){
          ser.createPriceLine({price:data[data.length-1].value,color,lineWidth:1,lineStyle:LC.LineStyle?.Dashed ?? 2,lineVisible:false,axisLabelVisible:true,title:label});
        }
      }
      return ser;
    };
    if(sr.length>1){mkLine('upper','#38bdf8',2,LC.LineStyle?.Dashed ?? 2,'مقاومة ديناميكية');mkLine('middle','#a78bfa',1,LC.LineStyle?.Solid ?? 0);mkLine('lower','#2dd4bf',2,LC.LineStyle?.Dashed ?? 2,'دعم ديناميكي');}
"""
assert old in s, "chart channel block not found"
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

sw=Path("static/service-worker.js")
t=sw.read_text(encoding="utf-8")
for old_cache in ["khalid-ai-v090-shell","khalid-ai-v100-shell","khalid-ai-v101-shell","khalid-ai-v102-shell"]:
    t=t.replace(old_cache,"khalid-ai-v103-shell")
sw.write_text(t,encoding="utf-8")
PY


# Full TASI universe selector: dynamic Saudi equity list, sector filter, search and local favorites.
RUN python - <<'PY'
from pathlib import Path

# ---------- backend ----------
p = Path("app_cloud.py")
s = p.read_text(encoding="utf-8")

old_display = '''def display_name(symbol: str) -> str:
    return KNOWN_SYMBOLS.get(symbol, f"السهم {symbol.replace('.SR','')}")
'''
new_display = '''DYNAMIC_SYMBOL_NAMES: dict[str, str] = {}
TASI_UNIVERSE_CACHE: dict[str, object] = {"loaded_at": 0.0, "items": []}
TASI_UNIVERSE_LOCK = threading.Lock()
TASI_SECTORS_AR = {
    "Basic Materials": "المواد الأساسية",
    "Communication Services": "الاتصالات والإعلام",
    "Consumer Cyclical": "السلع والخدمات الكمالية",
    "Consumer Defensive": "السلع الاستهلاكية",
    "Energy": "الطاقة",
    "Financial Services": "الخدمات المالية",
    "Healthcare": "الرعاية الصحية",
    "Industrials": "الصناعات والخدمات",
    "Real Estate": "العقارات",
    "Technology": "التقنية",
    "Utilities": "المرافق العامة",
}

def display_name(symbol: str) -> str:
    return KNOWN_SYMBOLS.get(symbol) or DYNAMIC_SYMBOL_NAMES.get(symbol) or f"السهم {symbol.replace('.SR','')}"

def _screen_saudi_equities(extra_query=None) -> list[dict[str, Any]]:
    from yfinance import EquityQuery
    clauses = [
        EquityQuery("eq", ["region", "sa"]),
        EquityQuery("eq", ["exchange", "SAU"]),
    ]
    if extra_query is not None:
        clauses.append(extra_query)
    query = EquityQuery("and", clauses)
    rows: list[dict[str, Any]] = []
    for offset in (0, 250, 500):
        response = yf.screen(query, offset=offset, size=250, sortField="ticker", sortAsc=True)
        quotes = response.get("quotes", []) if isinstance(response, dict) else []
        rows.extend(quotes)
        if len(quotes) < 250:
            break
    return rows

def load_tasi_universe(force: bool = False) -> list[dict[str, Any]]:
    now = time.time()
    cached = TASI_UNIVERSE_CACHE.get("items") or []
    loaded_at = float(TASI_UNIVERSE_CACHE.get("loaded_at") or 0.0)
    if cached and not force and now - loaded_at < 21600:
        return list(cached)

    with TASI_UNIVERSE_LOCK:
        cached = TASI_UNIVERSE_CACHE.get("items") or []
        loaded_at = float(TASI_UNIVERSE_CACHE.get("loaded_at") or 0.0)
        if cached and not force and now - loaded_at < 21600:
            return list(cached)

        base_quotes = _screen_saudi_equities()
        by_symbol: dict[str, dict[str, Any]] = {}
        for q in base_quotes:
            symbol = str(q.get("symbol") or "").upper().strip()
            if not symbol.endswith(".SR"):
                continue
            code = symbol[:-3]
            if len(code) != 4 or not code.isdigit():
                continue
            # Nomu symbols are 9xxx. Main-market equity/fund codes are below 9000.
            if int(code) >= 9000:
                continue
            name = str(q.get("shortName") or q.get("longName") or q.get("displayName") or "").strip()
            if not name:
                continue
            # Saudi Exchange treats REITs as funds, not TASI equities.
            if "REIT" in name.upper():
                continue
            by_symbol[symbol] = {
                "symbol": symbol,
                "code": code,
                "name": name,
                "sector_en": "",
                "sector_ar": "غير مصنف",
            }

        # Yahoo's base screener omits sector fields, so classify with 11 inexpensive sector screens.
        try:
            from yfinance import EquityQuery
            for sector_en, sector_ar in TASI_SECTORS_AR.items():
                sector_quotes = _screen_saudi_equities(EquityQuery("eq", ["sector", sector_en]))
                for q in sector_quotes:
                    symbol = str(q.get("symbol") or "").upper().strip()
                    if symbol in by_symbol:
                        by_symbol[symbol]["sector_en"] = sector_en
                        by_symbol[symbol]["sector_ar"] = sector_ar
        except Exception:
            # Sector classification is optional; the complete symbol list remains usable.
            pass

        items = sorted(by_symbol.values(), key=lambda x: int(x["code"]))
        for item in items:
            symbol = item["symbol"]
            code = item["code"]
            if symbol not in KNOWN_SYMBOLS:
                DYNAMIC_SYMBOL_NAMES[symbol] = f'{item["name"]} — {code}'
        TASI_UNIVERSE_CACHE["items"] = items
        TASI_UNIVERSE_CACHE["loaded_at"] = now
        return list(items)
'''
assert old_display in s, "display_name block not found"
s = s.replace(old_display, new_display, 1)

route_marker = '''@app.post("/api/select")
async def api_select(request: Request):
'''
route_block = '''@app.get("/api/symbols")
async def api_symbols():
    try:
        items = await asyncio.to_thread(load_tasi_universe)
        return JSONResponse(
            {"market": "TASI", "count": len(items), "items": items},
            headers={"Cache-Control": "no-store"},
        )
    except Exception as exc:
        fallback = []
        for symbol, label in KNOWN_SYMBOLS.items():
            fallback.append({
                "symbol": symbol,
                "code": symbol.replace(".SR", ""),
                "name": label.split(" — ")[0],
                "sector_en": "",
                "sector_ar": "غير مصنف",
            })
        return JSONResponse(
            {"market": "TASI", "count": len(fallback), "items": fallback, "warning": str(exc)},
            headers={"Cache-Control": "no-store"},
        )

@app.post("/api/select")
async def api_select(request: Request):
'''
assert route_marker in s, "api_select marker not found"
s = s.replace(route_marker, route_block, 1)
p.write_text(s, encoding="utf-8")

# ---------- frontend ----------
p = Path("static/index.html")
h = p.read_text(encoding="utf-8")

old_selector = '''  <div class="selector">
    <select id="quickSymbol" onchange="quickPick()">
      <option value="1320">أنابيب السعودية 1320</option>
      <option value="2222">أرامكو 2222</option>
      <option value="1120">الراجحي 1120</option>
      <option value="1180">الأهلي 1180</option>
      <option value="1010">الرياض 1010</option>
      <option value="1150">الإنماء 1150</option>
      <option value="2010">سابك 2010</option>
      <option value="1211">معادن 1211</option>
      <option value="7203">علم 7203</option>
      <option value="1820">بان 1820</option>
    </select>
    <input id="symbolInput" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="أو اكتب رمز السهم" value="1320" />
    <button id="selectBtn" onclick="selectSymbol()">اختيار السهم</button>
  </div>
'''
new_selector = '''  <div class="market-picker">
    <div class="market-picker-head">
      <div><b>كل أسهم تاسي</b><div class="micro">ابحث بالرمز أو اسم الشركة، ثم اختر السهم.</div></div>
      <span id="universeCount" class="statuschip">جاري التحميل…</span>
    </div>
    <div class="market-controls">
      <input id="marketSearch" type="search" autocomplete="off" placeholder="بحث: 4031 أو Ground Services" oninput="renderSymbolOptions()" />
      <select id="sectorFilter" onchange="renderSymbolOptions()">
        <option value="">كل القطاعات</option>
        <option value="__fav__">★ المفضلة</option>
      </select>
    </div>
    <div class="selector">
      <select id="quickSymbol" onchange="quickPick()">
        <option value="1320">جاري تحميل أسهم تاسي…</option>
      </select>
      <input id="symbolInput" inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="رمز السهم" value="1320" />
      <button id="selectBtn" onclick="selectSymbol()">اختيار السهم</button>
    </div>
    <div class="market-fav-row">
      <button id="favBtn" class="secondary" onclick="toggleFavorite()">☆ إضافة للمفضلة</button>
      <span id="symbolHint" class="micro">يمكنك أيضًا كتابة أي رمز سعودي من 4 أرقام.</span>
    </div>
  </div>
'''
assert old_selector in h, "old selector not found"
h = h.replace(old_selector, new_selector, 1)

css = '''
    .market-picker{margin:10px 0 14px;padding:11px;border:1px solid var(--line);border-radius:15px;background:#081426}
    .market-picker-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:9px}
    .market-controls{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:8px;margin-bottom:8px}
    .market-controls input,.market-controls select{width:100%;min-width:0}
    .market-fav-row{display:flex;align-items:center;gap:10px;justify-content:space-between;margin-top:8px}
    .market-fav-row button{width:auto;min-width:150px}
    #quickSymbol option{direction:rtl}
    @media(max-width:520px){
      .market-controls{grid-template-columns:1fr}
      .market-picker-head{align-items:flex-start}
      .market-fav-row{align-items:flex-start;flex-direction:column}
      .market-fav-row button{width:100%}
    }
'''
assert "</style>" in h
h = h.replace("</style>", css + "  </style>", 1)

old_globals = "let deferredPrompt=null, lastAction=null, currentUpdatedAt=null, lastChart=null, currentChartApi=null, currentResizeObserver=null;"
new_globals = old_globals + "\nlet tasiSymbols=[];"
assert old_globals in h
h = h.replace(old_globals, new_globals, 1)

old_quick = "function quickPick(){ $('symbolInput').value=$('quickSymbol').value; }"
new_quick = r'''function favoriteCodes(){
  try{const x=JSON.parse(localStorage.getItem('khalidFavSymbols')||'[]');return Array.isArray(x)?x.map(String):[];}catch(_){return []}
}
function saveFavoriteCodes(v){localStorage.setItem('khalidFavSymbols',JSON.stringify([...new Set(v.map(String))]));}
function currentCode(){return String($('symbolInput')?.value||'').trim();}
function updateFavButton(){
  const b=$('favBtn'); if(!b)return;
  const code=currentCode(), yes=favoriteCodes().includes(code);
  b.textContent=yes?'★ في المفضلة':'☆ إضافة للمفضلة';
}
function toggleFavorite(){
  const code=currentCode(); if(!/^\d{4}$/.test(code))return;
  let fav=favoriteCodes();
  fav=fav.includes(code)?fav.filter(x=>x!==code):[...fav,code];
  saveFavoriteCodes(fav); updateFavButton(); renderSymbolOptions();
}
function renderSymbolOptions(){
  const sel=$('quickSymbol'); if(!sel)return;
  const q=String($('marketSearch')?.value||'').trim().toLowerCase();
  const sector=String($('sectorFilter')?.value||'');
  const fav=favoriteCodes();
  let rows=tasiSymbols.filter(x=>{
    if(sector==='__fav__'&&!fav.includes(String(x.code)))return false;
    if(sector&&sector!=='__fav__'&&x.sector_en!==sector)return false;
    if(!q)return true;
    return (`${x.code} ${x.name||''} ${x.sector_ar||''}`).toLowerCase().includes(q);
  });
  const exact=tasiSymbols.find(x=>String(x.code)===q);
  if(exact&&rows.some(x=>String(x.code)===q)) $('symbolInput').value=String(exact.code);
  const cur=currentCode();
  sel.innerHTML=rows.map(x=>`<option value="${x.code}">${x.code} — ${x.name}${x.sector_ar&&x.sector_ar!=='غير مصنف'?' · '+x.sector_ar:''}</option>`).join('');
  if(!rows.length) sel.innerHTML='<option value="">لا توجد نتائج مطابقة</option>';
  if(rows.some(x=>String(x.code)===cur)) sel.value=cur;
  $('symbolHint').textContent=`النتائج: ${rows.length} من ${tasiSymbols.length} سهم`;
  updateFavButton();
}
async function loadSymbols(){
  try{
    const r=await fetch('/api/symbols',{cache:'no-store'});
    if(!r.ok)throw new Error('HTTP '+r.status);
    const d=await r.json();
    tasiSymbols=Array.isArray(d.items)?d.items:[];
    const sectors=[...new Map(tasiSymbols.filter(x=>x.sector_en).map(x=>[x.sector_en,x.sector_ar||x.sector_en])).entries()];
    const sf=$('sectorFilter');
    sf.innerHTML='<option value="">كل القطاعات</option><option value="__fav__">★ المفضلة</option>'+
      sectors.map(([en,ar])=>`<option value="${en}">${ar}</option>`).join('');
    $('universeCount').textContent=`${tasiSymbols.length} سهم`;
    renderSymbolOptions();
  }catch(e){
    $('universeCount').textContent='تعذر تحميل القائمة';
    $('symbolHint').textContent='القائمة غير متاحة مؤقتًا؛ ما زال اختيار الرمز يدويًا يعمل.';
  }
}
function quickPick(){
  const v=$('quickSymbol').value;
  if(v)$('symbolInput').value=v;
  updateFavButton();
}'''
assert old_quick in h, "quickPick function not found"
h = h.replace(old_quick, new_quick, 1)

old_render_piece = "if([...$('quickSymbol').options].some(o=>o.value===code)) $('quickSymbol').value=code;"
new_render_piece = old_render_piece + " updateFavButton();"
assert old_render_piece in h
h = h.replace(old_render_piece, new_render_piece, 1)

old_init = "load(); setInterval(load,20000);"
new_init = "load(); loadSymbols(); setInterval(load,20000);"
assert old_init in h
h = h.replace(old_init, new_init, 1)

p.write_text(h, encoding="utf-8")

sw = Path("static/service-worker.js")
t = sw.read_text(encoding="utf-8")
for old_cache in ["khalid-ai-v090-shell","khalid-ai-v100-shell","khalid-ai-v101-shell","khalid-ai-v102-shell","khalid-ai-v103-shell"]:
    t = t.replace(old_cache, "khalid-ai-v104-shell")
sw.write_text(t, encoding="utf-8")

assert '@app.get("/api/symbols")' in Path("app_cloud.py").read_text(encoding="utf-8")
html = Path("static/index.html").read_text(encoding="utf-8")
for token in ["كل أسهم تاسي","marketSearch","sectorFilter","toggleFavorite","loadSymbols"]:
    assert token in html, token
PY


# Arabic TASI directory + TTWO US-market support.
RUN python - <<'PY'
from pathlib import Path

# ---------- backend ----------
p = Path("app_cloud.py")
s = p.read_text(encoding="utf-8")

# Take-Two: explicit supported US symbol.
if 'KNOWN_SYMBOLS["TTWO"]' not in s:
    insert_at = s.index("DYNAMIC_SYMBOL_NAMES:")
    s = s[:insert_at] + 'KNOWN_SYMBOLS["TTWO"] = "تيك-تو إنتراكتيف سوفتوير — TTWO"\n\n' + s[insert_at:]

# Allow Saudi 4-digit symbols and TTWO.
start = s.index("def normalize_symbol(value: str) -> str:")
end = s.index("\nCURRENT_SYMBOL =", start)
s = s[:start] + '''def normalize_symbol(value: str) -> str:
    raw = (value or "").strip().upper().replace(" ", "")
    if raw == "TTWO":
        return "TTWO"
    if raw.endswith(".SR"):
        raw = raw[:-3]
    if not raw.isdigit() or len(raw) != 4:
        raise ValueError("اختر سهمًا سعوديًا من القائمة أو الرمز الأمريكي TTWO")
    return raw + ".SR"

def market_context_symbol(symbol: str) -> str:
    return "^IXIC" if symbol == "TTWO" else MARKET_SYMBOL

def symbol_market(symbol: str) -> str:
    return "NASDAQ" if symbol == "TTWO" else "TASI"

''' + s[end+1:]

# Use the correct benchmark for each market.
s = s.replace('fm = pool.submit(fetch, MARKET_SYMBOL, "5m", "60d")',
              'fm = pool.submit(fetch, market_context_symbol(symbol), "5m", "60d")')

# Data freshness must follow the selected market's trading session.
qstart = s.index("def assess_data_quality(df: pd.DataFrame)")
qend = s.index("\ndef research_snapshot", qstart)
quality = '''def assess_data_quality(df: pd.DataFrame, symbol: str | None = None) -> dict[str, Any]:
    if df is None or df.empty:
        return {'available':False,'score':0,'fresh':False,'label':'لا توجد بيانات'}
    ts=pd.to_datetime(df['timestamp'],utc=True,errors='coerce').dropna()
    if ts.empty:
        return {'available':False,'score':0,'fresh':False,'label':'توقيت البيانات غير صالح'}
    last=ts.iloc[-1].to_pydatetime()
    now=datetime.now(timezone.utc)
    age=max(0.0,(now-last).total_seconds()/60.0)
    selected = symbol or CURRENT_SYMBOL
    if selected == "TTWO":
        local=datetime.now(ZoneInfo('America/New_York'))
        market_open=(local.weekday() in [0,1,2,3,4]) and (
            (local.hour>9 or (local.hour==9 and local.minute>=30)) and local.hour<16
        )
    else:
        local=datetime.now(ZoneInfo('Asia/Riyadh'))
        market_open=(local.weekday() in [6,0,1,2,3]) and (
            (local.hour>10 or (local.hour==10 and local.minute>=0)) and
            (local.hour<15 or (local.hour==15 and local.minute<=0))
        )
    fresh=(age<=12.0) if market_open else True
    diffs=ts.diff().dt.total_seconds().div(60).dropna()
    intraday=diffs[(diffs>0)&(diffs<60)]
    spacing_ok=float((np.abs(intraday-5.0)<=1.2).mean()) if len(intraday) else 0.0
    v=pd.to_numeric(df['volume'],errors='coerce').tail(80)
    nonzero=float((v>0).mean()) if len(v) else 0.0
    o=df['open'].astype(float);h=df['high'].astype(float);l=df['low'].astype(float);c=df['close'].astype(float)
    ohlc_ok=float(((h>=pd.concat([o,c],axis=1).max(axis=1))&(l<=pd.concat([o,c],axis=1).min(axis=1))).tail(80).mean())
    score=100.0*(0.45*spacing_ok+0.30*nonzero+0.25*ohlc_ok)
    if market_open and not fresh: score*=0.45
    label='جيدة' if score>=85 and fresh else ('مقبولة' if score>=68 and fresh else 'تحذير')
    return {
        'available':True,'score':round(score,1),'fresh':bool(fresh),'label':label,
        'age_minutes':round(age,1),'market_open_now':bool(market_open),
        'spacing_ok_pct':round(spacing_ok*100,1),'nonzero_volume_pct':round(nonzero*100,1),
        'last_timestamp':str(ts.iloc[-1]),'market':symbol_market(selected)
    }

'''
s = s[:qstart] + quality + s[qend+1:]
s = s.replace("dq = assess_data_quality(df5)", "dq = assess_data_quality(df5, symbol)")

# Replace Yahoo-English directory with Arabic directory; Yahoo remains fallback only.
ustart = s.index("def load_tasi_universe(force: bool = False)")
uend = s.index('\n@app.get("/api/symbols")', ustart)
universe = r'''def _arabic_tasi_directory() -> list[dict[str, Any]]:
    import re
    import requests
    from bs4 import BeautifulSoup
    url = "https://tadawulallshareindex.com/all-shares-codes/"
    response = requests.get(
        url, timeout=20,
        headers={"User-Agent":"Mozilla/5.0 KhalidAITrader/1.0"}
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for tr in soup.find_all("tr"):
        cells = [x.get_text(" ", strip=True) for x in tr.find_all(["td","th"])]
        if len(cells) < 4:
            continue
        code = cells[0].strip()
        if not re.fullmatch(r"\d{4}", code):
            continue
        if int(code) >= 9000:
            continue
        name_ar = cells[1].strip()
        name_en = cells[2].strip()
        sector_ar = cells[3].strip() or "غير مصنف"
        if not name_ar or code in seen:
            continue
        seen.add(code)
        symbol = code + ".SR"
        items.append({
            "symbol": symbol,
            "code": code,
            "name": name_ar,
            "name_ar": name_ar,
            "name_en": name_en,
            "sector_en": sector_ar,
            "sector_ar": sector_ar,
            "market": "TASI",
        })
    if len(items) < 220:
        raise ValueError(f"دليل الأسماء العربية غير مكتمل: {len(items)}")
    return sorted(items, key=lambda x: int(x["code"]))

def _yahoo_tasi_fallback() -> list[dict[str, Any]]:
    base_quotes = _screen_saudi_equities()
    by_symbol: dict[str, dict[str, Any]] = {}
    for q in base_quotes:
        symbol = str(q.get("symbol") or "").upper().strip()
        if not symbol.endswith(".SR"):
            continue
        code = symbol[:-3]
        if len(code) != 4 or not code.isdigit() or int(code) >= 9000:
            continue
        name_en = str(q.get("shortName") or q.get("longName") or q.get("displayName") or "").strip()
        if not name_en or "REIT" in name_en.upper():
            continue
        known = KNOWN_SYMBOLS.get(symbol, "")
        name_ar = known.split(" — ")[0] if known else f"السهم {code}"
        by_symbol[symbol] = {
            "symbol":symbol,"code":code,"name":name_ar,"name_ar":name_ar,
            "name_en":name_en,"sector_en":"","sector_ar":"غير مصنف","market":"TASI"
        }
    return sorted(by_symbol.values(), key=lambda x:int(x["code"]))

def load_tasi_universe(force: bool = False) -> list[dict[str, Any]]:
    now=time.time()
    cached=TASI_UNIVERSE_CACHE.get("items") or []
    loaded_at=float(TASI_UNIVERSE_CACHE.get("loaded_at") or 0.0)
    if cached and not force and now-loaded_at < 21600:
        return list(cached)
    with TASI_UNIVERSE_LOCK:
        cached=TASI_UNIVERSE_CACHE.get("items") or []
        loaded_at=float(TASI_UNIVERSE_CACHE.get("loaded_at") or 0.0)
        if cached and not force and now-loaded_at < 21600:
            return list(cached)
        try:
            items=_arabic_tasi_directory()
        except Exception:
            items=_yahoo_tasi_fallback()
        for item in items:
            symbol=item["symbol"]; code=item["code"]; name=item["name"]
            DYNAMIC_SYMBOL_NAMES[symbol]=f"{name} — {code}"
        items.append({
            "symbol":"TTWO","code":"TTWO",
            "name":"تيك-تو إنتراكتيف سوفتوير",
            "name_ar":"تيك-تو إنتراكتيف سوفتوير",
            "name_en":"Take-Two Interactive Software, Inc.",
            "sector_en":"Interactive Entertainment",
            "sector_ar":"الألعاب والبرمجيات",
            "market":"NASDAQ",
        })
        TASI_UNIVERSE_CACHE["items"]=items
        TASI_UNIVERSE_CACHE["loaded_at"]=now
        return list(items)
'''
s = s[:ustart] + universe + s[uend:]

p.write_text(s, encoding="utf-8")

# ---------- frontend ----------
p = Path("static/index.html")
h = p.read_text(encoding="utf-8")

# Arabic-first instructions and allow TTWO.
h = h.replace(
    '<div><b>كل أسهم تاسي</b><div class="micro">ابحث بالرمز أو اسم الشركة، ثم اختر السهم.</div></div>',
    '<div><b>اختيار السهم</b><div class="micro">اختر من القائمة المنسدلة — أسهم تاسي بالعربي + Take-Two.</div></div>'
)
h = h.replace('placeholder="بحث: 4031 أو Ground Services"', 'placeholder="بحث: 4031 أو الخدمات الأرضية أو TTWO"')
h = h.replace('inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="رمز السهم"',
              'inputmode="text" maxlength="5" placeholder="رمز السهم"')

# Favorites accept Saudi symbols and TTWO.
h = h.replace("if(!/^\\d{4}$/.test(code))return;",
              "if(!/^(\\d{4}|TTWO)$/i.test(code))return;")

# Search Arabic/English names and market.
old_search = "return (`${x.code} ${x.name||''} ${x.sector_ar||''}`).toLowerCase().includes(q);"
new_search = "return (`${x.code} ${x.name||''} ${x.name_ar||''} ${x.name_en||''} ${x.sector_ar||''} ${x.market||''}`).toLowerCase().includes(q);"
if old_search in h:
    h = h.replace(old_search, new_search, 1)

# Dropdown grouped by Saudi / US markets.
old_options = "sel.innerHTML=rows.map(x=>`<option value=\"${x.code}\">${x.code} — ${x.name}${x.sector_ar&&x.sector_ar!=='غير مصنف'?' · '+x.sector_ar:''}</option>`).join('');"
new_options = """const sa=rows.filter(x=>x.market!=='NASDAQ'), us=rows.filter(x=>x.market==='NASDAQ');
  sel.innerHTML=
    (sa.length?'<optgroup label="السوق السعودي — تاسي">'+sa.map(x=>`<option value="${x.code}">${x.code} — ${x.name}${x.sector_ar&&x.sector_ar!=='غير مصنف'?' · '+x.sector_ar:''}</option>`).join('')+'</optgroup>':'')+
    (us.length?'<optgroup label="السوق الأمريكي — ناسداك">'+us.map(x=>`<option value="${x.code}">${x.code} — ${x.name}</option>`).join('')+'</optgroup>':'');"""
assert old_options in h, "dropdown options block not found"
h = h.replace(old_options, new_options, 1)

# Count only TASI shares, while making TTWO explicit.
old_count = "$('universeCount').textContent=`${tasiSymbols.length} سهم`;"
new_count = """const tasiCount=tasiSymbols.filter(x=>x.market!=='NASDAQ').length;
    $('universeCount').textContent=`${tasiCount} تاسي + TTWO`;"""
assert old_count in h, "count label block not found"
h = h.replace(old_count, new_count, 1)

# Do not mix TTWO sector into the TASI sector filter.
old_sectors = "const sectors=[...new Map(tasiSymbols.filter(x=>x.sector_en).map(x=>[x.sector_en,x.sector_ar||x.sector_en])).entries()];"
new_sectors = "const sectors=[...new Map(tasiSymbols.filter(x=>x.market!=='NASDAQ'&&x.sector_en).map(x=>[x.sector_en,x.sector_ar||x.sector_en])).entries()];"
assert old_sectors in h
h = h.replace(old_sectors, new_sectors, 1)

# Validation accepts TTWO.
old_validation = "if(!/^\\d{4}$/.test(code)){ $('error').textContent='اكتب رمز تداول من 4 أرقام مثل 1320 أو 2222'; return;}"
new_validation = "if(!/^(\\d{4}|TTWO)$/i.test(code)){ $('error').textContent='اختر سهمًا من القائمة أو اكتب رمزًا سعوديًا من 4 أرقام أو TTWO'; return;}"
assert old_validation in h
h = h.replace(old_validation, new_validation, 1)

# Uppercase free-text symbol before posting.
h = h.replace("const code=$('symbolInput').value.trim(), b=$('selectBtn');",
              "const code=$('symbolInput').value.trim().toUpperCase(), b=$('selectBtn');",1)

# Currency label switches correctly for TTWO.
h = h.replace('<small style="font-size:14px;color:#9fb1c9">ر.س</small>',
              '<small id="currencyLabel" style="font-size:14px;color:#9fb1c9">ر.س</small>')
needle = "$('symbolName').textContent=d.name||d.symbol||'—';"
assert needle in h
h = h.replace(needle, needle + " if($('currencyLabel')) $('currencyLabel').textContent=(d.symbol==='TTWO'?'
ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    MALLOC_ARENA_MAX=2

EXPOSE 8080
CMD ["sh","-c","exec python -m uvicorn app_cloud:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
:'ر.س');", 1)

# Friendlier result text.
h = h.replace("$('symbolHint').textContent=`النتائج: ${rows.length} من ${tasiSymbols.length} سهم`;",
              "$('symbolHint').textContent=`النتائج: ${rows.length} — اختر السهم من القائمة المنسدلة`;")

p.write_text(h, encoding="utf-8")

# PWA cache bust.
sw=Path("static/service-worker.js")
t=sw.read_text(encoding="utf-8")
for old_cache in ["khalid-ai-v104-shell","khalid-ai-v103-shell","khalid-ai-v102-shell"]:
    t=t.replace(old_cache,"khalid-ai-v105-shell")
sw.write_text(t,encoding="utf-8")

# Assertions.
app=Path("app_cloud.py").read_text(encoding="utf-8")
html=Path("static/index.html").read_text(encoding="utf-8")
for token in ['KNOWN_SYMBOLS["TTWO"]','market_context_symbol','America/New_York','_arabic_tasi_directory','"market":"NASDAQ"']:
    assert token in app, token
for token in ['السوق السعودي — تاسي','السوق الأمريكي — ناسداك','TTWO','currencyLabel','الخدمات الأرضية']:
    assert token in html, token
PY

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
