from pathlib import Path

# Patch T1/T2/STOP so displayed levels are executable market prices,
# not arbitrary geometry decimals rounded after the fact.

p=Path("app_cloud.py")
s=p.read_text(encoding="utf-8")

anchor='''def symbol_market(symbol: str) -> str:
    return "NASDAQ" if symbol == "TTWO" else "TASI"

'''
helper='''def symbol_market(symbol: str) -> str:
    return "NASDAQ" if symbol == "TTWO" else "TASI"

def market_tick_size(symbol: str, price: float) -> float:
    p=float(price or 0.0)
    if symbol == "TTWO":
        return 0.01
    if p < 25:
        return 0.01
    if p < 50:
        return 0.02
    if p < 100:
        return 0.05
    if p < 250:
        return 0.10
    if p < 500:
        return 0.20
    return 0.50

def executable_price(value: float | None, symbol: str, direction: str = "nearest") -> float | None:
    if value is None or not np.isfinite(float(value)):
        return None
    v=float(value)
    tick=market_tick_size(symbol,v)
    units=v/tick
    if direction == "up":
        units=np.ceil(units-1e-10)
    elif direction == "down":
        units=np.floor(units+1e-10)
    else:
        units=np.round(units)
    return round(float(units*tick),2)

'''
assert anchor in s, "symbol_market anchor missing"
s=s.replace(anchor,helper,1)

old_rr='''        if target1 is not None and stop is not None:
            risk=price-stop; reward=target1-price
            if risk>1e-9 and reward>0: rr=reward/risk
'''
new_rr='''        if target1 is not None:
            target1=executable_price(target1,CURRENT_SYMBOL,"up")
        if target2 is not None:
            target2=executable_price(target2,CURRENT_SYMBOL,"up")
        if stop is not None:
            stop=executable_price(stop,CURRENT_SYMBOL,"down")
        if target1 is not None and stop is not None:
            risk=price-stop; reward=target1-price
            if risk>1e-9 and reward>0:
                rr=reward/risk
            else:
                rr=None
'''
assert old_rr in s, "risk/reward block missing"
s=s.replace(old_rr,new_rr,1)

old_fields="""        'breakout_confirm_above':round(upper+buffer_,2),'breakdown_confirm_below':round(lower-buffer_,2),'technical_invalidation':round(invalidation,2) if geometry_valid else None,
        'research_target_1':round(float(target1),2) if target1 is not None else None,'research_target_2':round(float(target2),2) if target2 is not None else None,
        'research_stop':round(float(stop),2) if stop is not None else None,'reward_risk_to_t1':round(float(rr),2) if rr is not None and np.isfinite(rr) else None,
"""
new_fields="""        'breakout_confirm_above':executable_price(upper+buffer_,CURRENT_SYMBOL,'up'),'breakdown_confirm_below':executable_price(lower-buffer_,CURRENT_SYMBOL,'down'),'technical_invalidation':executable_price(invalidation,CURRENT_SYMBOL,'down') if geometry_valid else None,
        'research_target_1':target1,'research_target_2':target2,
        'research_stop':stop,'reward_risk_to_t1':round(float(rr),2) if rr is not None and np.isfinite(rr) else None,
        'target1_pct':round(((target1/price)-1)*100,2) if target1 is not None and price else None,
        'target2_pct':round(((target2/price)-1)*100,2) if target2 is not None and price else None,
        'stop_pct':round(((stop/price)-1)*100,2) if stop is not None and price else None,
        'plan_valid':bool(target1 is not None and target1>price and (stop is None or stop<price)),
        'tick_size':market_tick_size(CURRENT_SYMBOL,price),
"""
assert old_fields in s, "target fields missing"
s=s.replace(old_fields,new_fields,1)
p.write_text(s,encoding="utf-8")

# Frontend clarity.
p=Path("static/index.html")
h=p.read_text(encoding="utf-8")

needle="const ch=d.channel||{};"
replacement="const ch=d.channel||{}; const lvl=(v,p)=>v==null?'—':Number(v).toFixed(2)+(p==null?'':' ('+(Number(p)>=0?'+':'')+Number(p).toFixed(2)+'%)');"
assert needle in h, "channel object line missing"
h=h.replace(needle,replacement,1)

h=h.replace("$('researchTarget1').textContent=ch.research_target_1??'—';","$('researchTarget1').textContent=lvl(ch.research_target_1,ch.target1_pct);",1)
h=h.replace("$('researchTarget2').textContent=ch.research_target_2??'—';","$('researchTarget2').textContent=lvl(ch.research_target_2,ch.target2_pct);",1)
h=h.replace("$('researchStop').textContent=ch.research_stop??'—';","$('researchStop').textContent=lvl(ch.research_stop,ch.stop_pct);",1)

old_lines="""      priceLine(ch.research_target_1,'#fbbf24','T1');
      priceLine(ch.research_target_2,'#f59e0b','T2',LC.LineStyle?.Dotted ?? 1);
      priceLine(ch.research_stop,'#fb7185','STOP');
"""
new_lines="""      if(ch.plan_valid!==false){
        priceLine(ch.research_target_1,'#fbbf24','T1 فني');
        priceLine(ch.research_target_2,'#f59e0b','T2 فني',LC.LineStyle?.Dotted ?? 1);
        priceLine(ch.research_stop,'#fb7185','إبطال فني');
      }
"""
assert old_lines in h, "chart price lines missing"
h=h.replace(old_lines,new_lines,1)

# Make the scenario explicitly research/technical.
scenario_tail=":'بيانات غير كافية'; $('channelState').textContent="
scenario_new=":'بيانات غير كافية'; if(ch.available&&ch.plan_valid===false){$('chartScenario').textContent+=' · ⚠️ مستويات الخطة غير صالحة بعد تقريبها لسعر التنفيذ';} else if(ch.available&&ch.reward_risk_to_t1!=null&&Number(ch.reward_risk_to_t1)<1){$('chartScenario').textContent+=' · ⚠️ عائد/مخاطرة T1 ضعيف ('+Number(ch.reward_risk_to_t1).toFixed(2)+'×) · مستويات فنية وليست توصية';} else if(ch.available){$('chartScenario').textContent+=' · المستويات فنية استرشادية وليست توصية';} $('channelState').textContent="
assert scenario_tail in h, "scenario insertion point missing"
h=h.replace(scenario_tail,scenario_new,1)

p.write_text(h,encoding="utf-8")

# PWA cache bump.
sw=Path("static/service-worker.js")
t=sw.read_text(encoding="utf-8")
for old in ["khalid-ai-v106-shell","khalid-ai-v105-shell","khalid-ai-v104-shell","khalid-ai-v103-shell"]:
    t=t.replace(old,"khalid-ai-v107-shell")
sw.write_text(t,encoding="utf-8")
