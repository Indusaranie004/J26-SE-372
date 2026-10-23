"""
Rerun consistency check for the seed-stage ablation.
Runs tests/run_ablation.py twice and compares every reported metric.
Passes if all metrics agree to 3 decimal places; also reports the largest difference.
Writes the verdict to evidence/ablation_study/rerun_consistency_check.txt

Usage (from component-b root):
  GT1_PATH=data/gt1_expert.json python3 tests/rerun_consistency_check.py
"""
import datetime, json, os, shutil, subprocess, sys

OUT    = "evidence/ablation_study"
RESULT = os.path.join(OUT, "ablation_results.json")
RUN1   = os.path.join(OUT, "run1.json")
TOL    = 0.0005          # agreement to 3 decimal places
env    = {**os.environ, "GT1_PATH": os.getenv("GT1_PATH", "data/gt1_expert.json")}

def run():
    subprocess.run([sys.executable, "tests/run_ablation.py"], env=env, check=True,
                   stdout=subprocess.DEVNULL)

print("Run 1 ..."); run(); shutil.copy(RESULT, RUN1)
print("Run 2 ..."); run()

a, b = json.load(open(RUN1)), json.load(open(RESULT))
diffs = []
for row, subs in a["rows"].items():
    for sub, metrics in subs.items():
        for m, v in metrics.items():
            d = abs(v - b["rows"][row][sub][m])
            if d > 0:
                diffs.append((d, row.strip(), sub, m, v, b["rows"][row][sub][m]))

max_d = max((d[0] for d in diffs), default=0.0)
ok    = max_d <= TOL
stamp = f"{datetime.datetime.now():%Y-%m-%d %H:%M}"
lines = [f"{'Consistent' if ok else 'NOT consistent'}: all metrics agree to 3 decimal places "
         f"(max difference {max_d:.4f}) ({stamp}, GT1_PATH={env['GT1_PATH']})"]
lines += [f"  {sub:12} {m:5} {row}: {x} vs {y}" for _, row, sub, m, x, y in sorted(diffs, reverse=True)]
print("\n".join(lines))
with open(os.path.join(OUT, "rerun_consistency_check.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
sys.exit(0 if ok else 1)

#GT1_PATH=data/gt1_expert.json python3 tests/rerun_consistency_check.py