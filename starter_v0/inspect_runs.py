
import json
import sys
from pathlib import Path

version = sys.argv[1] if len(sys.argv) > 1 else "v0"
files = sorted(Path("runs").glob(f"{version}_*.json"))

if not files:
    raise SystemExit(f"Không tìm thấy run của {version}")

path = files[-1]
data = json.loads(path.read_text(encoding="utf-8"))

print("RUN FILE:", path)
print("SUMMARY:")
print(json.dumps(data["summary"], indent=2, ensure_ascii=False))

for case in data["results"]:
    result = case["result"]
    if result["passed"]:
        continue

    print("\nCASE:", case["id"])
    print("EXPECTED:", json.dumps(case["expect"], ensure_ascii=False))
    print("ACTUAL:", json.dumps(
        result["actual_tool_calls"], ensure_ascii=False
    ))
    print("MISMATCH:", result["observed_mismatch"])
    print("FAILURES:", result["failures"])
