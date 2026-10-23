"""
Rerun consistency check for the evaluation scripts.
Runs the chosen evaluation twice and compares every numeric result.
Passes if all metrics agree to 3 decimal places; also reports the largest difference.

Usage (from component-b root):
  GT1_PATH=data/gt1_expert.json python3 tests/rerun_consistency_check.py              # seed-stage ablation
  GT2_PATH=data/gt2_expert.json python3 tests/rerun_consistency_check.py traversal    # graph traversal
  GT1_PATH=data/gt1_expert.json GT2_PATH=data/gt2_expert.json python3 tests/rerun_consistency_check.py e2e   # end-to-end traversal
"""
import datetime, json, os, shutil, subprocess, sys

TARGETS = {
    "ablation":  ("tests/run_ablation.py",           "evidence/ablation_study",  "ablation_results.json"),
    "traversal": ("tests/run_traversal_eval.py",     "evidence/graph_traversal", "gt2_results.json"),
    "e2e":       ("tests/run_e2e_traversal_eval.py", "evidence/graph_traversal", "e2e_traversal_results.json"),
}
target = sys.argv[1] if len(sys.argv) > 1 else "ablation"
SCRIPT, OUT, NAME = TARGETS[target]
RESULT, RUN1 = os.path.join(OUT, NAME), os.path.join(OUT, "run1.json")
TOL = 0.0005          # agreement to 3 decimal places
env = {**os.environ,
       "GT1_PATH": os.getenv("GT1_PATH", "data/gt1_expert.json"),
       "GT2_PATH": os.getenv("GT2_PATH", "data/gt2_expert.json")}

def run():
    subprocess.run([sys.executable, SCRIPT], env=env, check=True, stdout=subprocess.DEVNULL)

def leaves(x, path=""):
    """Yield (path, value) for every leaf value in nested JSON."""
    if isinstance(x, dict):
        for k, v in x.items(): yield from leaves(v, f"{path}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, x

print(f"[{target}] Run 1 ..."); run(); shutil.copy(RESULT, RUN1)
print(f"[{target}] Run 2 ..."); run()

a = dict(leaves(json.load(open(RUN1))))
b = dict(leaves(json.load(open(RESULT))))
diffs, mismatched = [], []
for k in sorted(set(a) | set(b)):
    x, y = a.get(k), b.get(k)
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
        if abs(x - y) > 0: diffs.append((abs(x - y), k, x, y))
    elif x != y:
        mismatched.append((k, x, y))

max_d = max((d[0] for d in diffs), default=0.0)
ok = max_d <= TOL and not mismatched
lines = [f"{'Consistent' if ok else 'NOT consistent'}: all metrics agree to 3 decimal places "
         f"(max difference {max_d:.4f}) ({datetime.datetime.now():%Y-%m-%d %H:%M}, {target})"]
lines += [f"  {k}: {x} vs {y}" for _, k, x, y in sorted(diffs, reverse=True)]
lines += [f"  non-numeric difference at {k}: {x} vs {y}" for k, x, y in mismatched]
print("\n".join(lines))
with open(os.path.join(OUT, f"rerun_consistency_check_{target}.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
sys.exit(0 if ok else 1)

#GT1_PATH=data/gt1_expert.json GT2_PATH=data/gt2_expert.json python3 tests/rerun_consistency_check.py e2e