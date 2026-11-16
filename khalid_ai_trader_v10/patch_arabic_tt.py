from pathlib import Path

# This patch runs after the base v1.0 Pro bundle and the existing full-TASI patch.
# It makes the selector Arabic-first and adds correct US-market support for TTWO.

# ---------- backend ----------
p = Path("app_cloud.py")
s = p.read_text(encoding="utf-8")

if 'KNOWN_SYMBOLS["TTWO"]' not in s:
    insert_at = s.index("DYNAMIC_SYMBOL_NAMES:")
    s = (
        s[:insert_at]
        + 'KNOWN_SYMBOLS["TTWO"] = "تيك-تو إنتراكتيف سوفتوير — TTWO"\n\n'
        + s[insert_at:]
    )

# Saudi 4-digit symbols + explicitly supported US ticker TTWO.
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

''' + s[end + 1 :]

# Correct benchmark per market.
s = s.replace(
    'fm = pool.submit(fetch, MARKET_SYMBOL, "5m", "60d")',
    'fm = pool.submit(fetch, market_context_symbol(symbol), "5m", "60d")',
)

# Correct session freshness per market.
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
    selected=symbol or CURRENT_SYMBOL
    if selected == "TTWO":
        local=datetime.now(ZoneInfo('America/New_York'))
        market_open=(local.weekday() in [0,1,2,3,4]) and (
            (local.hour>9 or (local.hour==9 and local.minute>=30)) and
            local.hour<16
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
    if market_open and not fresh:
        score*=0.45
    label='جيدة' if score>=85 and fresh else ('مقبولة' if score>=68 and fresh else 'تحذير')
    return {
        'available':True,'score':round(score,1),'fresh':bool(fresh),'label':label,
        'age_minutes':round(age,1),'market_open_now':bool(market_open),
        'spacing_ok_pct':round(spacing_ok*100,1),'nonzero_volume_pct':round(nonzero*100,1),
        'last_timestamp':str(ts.iloc[-1]),'market':symbol_market(selected)
    }

'''
s = s[:qstart] + quality + s[qend + 1 :]
s = s.replace("dq = assess_data_quality(df5)", "dq = assess_data_quality(df5, symbol)")

# Arabic directory for TASI.
ustart = s.index("def load_tasi_universe(force: bool = False)")
uend = s.index("\ndef normalize_symbol", ustart)
universe = '''def _arabic_tasi_directory() -> list[dict[str, Any]]:
    import re
    import requests
    from bs4 import BeautifulSoup
    url = "https://tadawulallshareindex.com/all-shares-codes/"
    response = requests.get(
        url,
        timeout=20,
        headers={"User-Agent":"Mozilla/5.0 KhalidAITrader/1.0"},
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
        if not re.fullmatch(r"\\d{4}", code):
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
            "symbol":symbol,
            "code":code,
            "name":name_ar,
            "name_ar":name_ar,
            "name_en":name_en,
            "sector_en":sector_ar,
            "sector_ar":sector_ar,
            "market":"TASI",
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
            "symbol":symbol,
            "code":code,
            "name":name_ar,
            "name_ar":name_ar,
            "name_en":name_en,
            "sector_en":"",
            "sector_ar":"غير مصنف",
            "market":"TASI",
        }
    return sorted(by_symbol.values(), key=lambda x: int(x["code"]))

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
            symbol=item["symbol"]
            code=item["code"]
            name=item["name"]
            DYNAMIC_SYMBOL_NAMES[symbol]=f"{name} — {code}"
        items.append({
            "symbol":"TTWO",
            "code":"TTWO",
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
s = s.replace('{"market": "TASI", "count": len(items), "items": items}',
              '{"market": "MULTI", "count": len(items), "items": items}')
p.write_text(s, encoding="utf-8")

# ---------- frontend ----------
p = Path("static/index.html")
h = p.read_text(encoding="utf-8")

h = h.replace(
    '<div><b>كل أسهم تاسي</b><div class="micro">ابحث بالرمز أو اسم الشركة، ثم اختر السهم.</div></div>',
    '<div><b>اختيار السهم</b><div class="micro">اختر من القائمة المنسدلة — أسهم تاسي بالعربي + Take-Two.</div></div>',
)
h = h.replace(
    'placeholder="بحث: 4031 أو Ground Services"',
    'placeholder="بحث: 4031 أو الخدمات الأرضية أو TTWO"',
)
h = h.replace(
    'inputmode="numeric" pattern="[0-9]*" maxlength="4" placeholder="رمز السهم"',
    'inputmode="text" maxlength="5" placeholder="رمز السهم"',
)
h = h.replace(
    '<small style="font-size:14px;color:#9fb1c9">ر.س</small>',
    '<small id="currencyLabel" style="font-size:14px;color:#9fb1c9">ر.س</small>',
)

# Replace selector helper functions as one coherent block.
fstart = h.index("function favoriteCodes(){")
fend = h.index("async function pollChange", fstart)
frontend_functions = r'''function favoriteCodes(){
  try{const x=JSON.parse(localStorage.getItem('khalidFavSymbols')||'[]');return Array.isArray(x)?x.map(String):[];}catch(_){return []}
}
function saveFavoriteCodes(v){localStorage.setItem('khalidFavSymbols',JSON.stringify([...new Set(v.map(String))]));}
function currentCode(){return String($('symbolInput')?.value||'').trim().toUpperCase();}
function updateFavButton(){
  const b=$('favBtn'); if(!b)return;
  const code=currentCode(), yes=favoriteCodes().includes(code);
  b.textContent=yes?'★ في المفضلة':'☆ إضافة للمفضلة';
}
function toggleFavorite(){
  const code=currentCode();
  if(!/^(\\d{4}|TTWO)$/i.test(code))return;
  let fav=favoriteCodes();
  fav=fav.includes(code)?fav.filter(x=>x!==code):[...fav,code];
  saveFavoriteCodes(fav); updateFavButton(); renderSymbolOptions();
}
function renderSymbolOptions(){
  const sel=$('quickSymbol'); if(!sel)return;
  const q=String($('marketSearch')?.value||'').trim().toLowerCase();
  const sector=String($('sectorFilter')?.value||'');
  const fav=favoriteCodes();
  let rows=tasiSymbols.filter(function(x){
    if(sector==='__fav__'&&!fav.includes(String(x.code)))return false;
    if(sector&&sector!=='__fav__'&&x.sector_ar!==sector)return false;
    if(!q)return true;
    const hay=(String(x.code)+' '+(x.name||'')+' '+(x.name_ar||'')+' '+(x.name_en||'')+' '+(x.sector_ar||'')+' '+(x.market||'')).toLowerCase();
    return hay.includes(q);
  });
  const exact=tasiSymbols.find(function(x){return String(x.code).toLowerCase()===q;});
  if(exact&&rows.some(function(x){return String(x.code).toLowerCase()===q;})) $('symbolInput').value=String(exact.code);
  const cur=currentCode();
  const sa=rows.filter(function(x){return x.market!=='NASDAQ';});
  const us=rows.filter(function(x){return x.market==='NASDAQ';});
  let html='';
  if(sa.length){
    html+='<optgroup label="السوق السعودي — تاسي">';
    html+=sa.map(function(x){
      return '<option value="'+x.code+'">'+x.code+' — '+x.name+(x.sector_ar&&x.sector_ar!=='غير مصنف'?' · '+x.sector_ar:'')+'</option>';
    }).join('');
    html+='</optgroup>';
  }
  if(us.length){
    html+='<optgroup label="السوق الأمريكي — ناسداك">';
    html+=us.map(function(x){return '<option value="'+x.code+'">'+x.code+' — '+x.name+'</option>';}).join('');
    html+='</optgroup>';
  }
  sel.innerHTML=html||'<option value="">لا توجد نتائج مطابقة</option>';
  if(rows.some(function(x){return String(x.code).toUpperCase()===cur;})) sel.value=cur;
  $('symbolHint').textContent='النتائج: '+rows.length+' — اختر السهم من القائمة المنسدلة';
  updateFavButton();
}
async function loadSymbols(){
  try{
    const r=await fetch('/api/symbols',{cache:'no-store'});
    if(!r.ok)throw new Error('HTTP '+r.status);
    const d=await r.json();
    tasiSymbols=Array.isArray(d.items)?d.items:[];
    const sectors=[...new Set(tasiSymbols.filter(function(x){return x.market!=='NASDAQ'&&x.sector_ar;}).map(function(x){return x.sector_ar;}))];
    const sf=$('sectorFilter');
    sf.innerHTML='<option value="">كل القطاعات</option><option value="__fav__">★ المفضلة</option>'+
      sectors.map(function(ar){return '<option value="'+ar+'">'+ar+'</option>';}).join('');
    const tasiCount=tasiSymbols.filter(function(x){return x.market!=='NASDAQ';}).length;
    $('universeCount').textContent=tasiCount+' تاسي + TTWO';
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
}
'''
h = h[:fstart] + frontend_functions + h[fend:]

# Replace selectSymbol with TTWO-aware validation.
sstart = h.index("async function selectSymbol(){")
send = h.index("\nasync function retrain()", sstart)
select_fn = r'''async function selectSymbol(){
  const code=$('symbolInput').value.trim().toUpperCase(), b=$('selectBtn');
  if(!/^(\\d{4}|TTWO)$/i.test(code)){
    $('error').textContent='اختر سهمًا من القائمة أو اكتب رمزًا سعوديًا من 4 أرقام أو TTWO';
    return;
  }
  b.disabled=true;b.textContent='جاري التحويل…';$('error').textContent='';
  try{
    const r=await fetch('/api/select',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol:code})});
    const d=await r.json();
    if(!r.ok)throw new Error(d.error||('HTTP '+r.status));
    render(d);
    const before=d.updated_at;
    await pollChange(before,14);
    try{renderChart(await getChart());}catch(_){}
  }catch(e){
    $('error').textContent='تعذر اختيار السهم: '+e.message
  }finally{
    b.disabled=false;b.textContent='اختيار السهم';
  }
}
'''
h = h[:sstart] + select_fn + h[send+1:]

# Currency in hero.
needle = "$('symbolName').textContent=d.name||d.symbol||'—';"
assert needle in h
replacement = needle + " if($('currencyLabel')) $('currencyLabel').textContent=(d.symbol==='TTWO'?'$':'ر.س');"
h = h.replace(needle, replacement, 1)

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
