from pathlib import Path
import re, ast, inspect, json

src = Path("/tmp/khalid/khalid_v100/app_cloud.py").read_text(encoding="utf-8")
html = Path("/tmp/khalid/khalid_v100/static/index.html").read_text(encoding="utf-8")

print("=== MODEL VERSION / GLOBAL SYMBOL CANDIDATES ===")
for line in src.splitlines():
    if any(k in line for k in ["MODEL_VERSION", "DEFAULT_SYMBOL", "MARKET_SYMBOL"]):
        print(line)

symbols = sorted(set(re.findall(r"(?<!\d)(\d{4})\.SR", src + "\n" + html)))
print("=== SYMBOLS IN SOURCE ===")
print("count=", len(symbols))
print(",".join(symbols))

print("=== QUICK SELECT OPTIONS ===")
for m in re.finditer(r'<option[^>]*value=["\']([^"\']+)["\'][^>]*>(.*?)</option>', html, flags=re.I|re.S):
    v = re.sub(r"<.*?>", "", m.group(1)).strip()
    label = re.sub(r"<.*?>", "", m.group(2)).strip()
    if v:
        print(v, "|", label)

print("=== QUALIFIED CONTEXT ===")
lines = src.splitlines()
for i,line in enumerate(lines):
    if "qualified" in line.lower() or "profit_factor" in line.lower() or "balanced_accuracy" in line.lower():
        if any(k in line.lower() for k in ["qualified", "profit_factor", "balanced_accuracy"]):
            print(f"--- {i+1} ---")
            for j in range(max(0,i-6), min(len(lines),i+10)):
                print(f"{j+1:04d}: {lines[j]}")

print("=== API SELECT CONTEXT ===")
for i,line in enumerate(lines):
    if "/api/select" in line or "def select" in line:
        print(f"--- {i+1} ---")
        for j in range(max(0,i-8), min(len(lines),i+35)):
            print(f"{j+1:04d}: {lines[j]}")

print("=== TRAIN / PIPELINE FUNCTION DEFINITIONS ===")
for i,line in enumerate(lines):
    if re.match(r"^def\s+.*(train|pipeline|refresh|fit|walk|quality|qualif)", line, flags=re.I):
        print(f"{i+1:04d}: {line}")
