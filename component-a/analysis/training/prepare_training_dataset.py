import csv, json, random
from collections import defaultdict

LABEL2ID = {
    "followed":      0,
    "distinguished": 1,
    "overruled":     2,
    "doubted":       3,
    "none":          4
}

# Load annotations
rows = list(csv.DictReader(
    open("analysis/annotation/annotation_final.csv", encoding="utf-8")
))

# Filter — only rows with a label
labelled = []
for r in rows:
    label = r.get("label", "").strip().lower()
    text  = r.get("text", "").strip()
    if label in LABEL2ID and len(text) > 20:
        labelled.append({
            "text":      text,
            "label":     LABEL2ID[label],
            "label_str": label,
            "doc_id":    r.get("doc_id", "")
        })

print(f"Total labelled examples: {len(labelled)}")
print()
for label in ["followed","distinguished","overruled","doubted","none"]:
    count = len([r for r in labelled if r["label_str"] == label])
    print(f"  {label}: {count}")

# Stratified split — ensure each class has test examples
random.seed(42)
by_label = defaultdict(list)
for item in labelled:
    by_label[item["label_str"]].append(item)

train, test = [], []
for label, items in by_label.items():
    random.shuffle(items)
    if len(items) <= 3:
        # Very few examples — put 1 in test, rest in train
        test.append(items[0])
        train.extend(items[1:])
    else:
        split = max(1, int(len(items) * 0.2))
        test.extend(items[:split])
        train.extend(items[split:])

random.shuffle(train)
random.shuffle(test)

print(f"\nTrain: {len(train)}")
print(f"Test:  {len(test)}")

# Save
with open("analysis/training/train.json", "w", encoding="utf-8") as f:
    json.dump(train, f, indent=2, ensure_ascii=False)

with open("analysis/training/test.json", "w", encoding="utf-8") as f:
    json.dump(test, f, indent=2, ensure_ascii=False)

print("\nSaved to analysis/training/train.json and analysis/training/test.json")

print("\nTrain distribution:")
for label in ["followed","distinguished","overruled","doubted","none"]:
    count = len([r for r in train if r["label_str"] == label])
    print(f"  {label}: {count}")

print("\nTest distribution:")
for label in ["followed","distinguished","overruled","doubted","none"]:
    count = len([r for r in test if r["label_str"] == label])
    print(f"  {label}: {count}")