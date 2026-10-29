import json, glob, os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db     = client["lk_legal"]
cases  = db["cases"]
stubs  = db["stubs"]

# Upload cases
case_files = glob.glob("corpus/cases/*.json")
print(f"Uploading {len(case_files)} case files...")

batch = []
for path in case_files:
    rec = json.load(open(path, encoding="utf-8"))
    rec["_id"] = rec["doc_id"]  # use doc_id as MongoDB _id
    batch.append(rec)
    if len(batch) >= 100:
        cases.insert_many(batch, ordered=False)
        print(f"  Uploaded {len(batch)} cases...")
        batch = []

if batch:
    cases.insert_many(batch, ordered=False)

print(f"Total cases uploaded: {cases.count_documents({})}")

# Upload stubs
stub_files = glob.glob("corpus/stubs/*.json")
print(f"\nUploading {len(stub_files)} stub files...")

batch = []
for path in stub_files:
    rec = json.load(open(path, encoding="utf-8"))
    rec["_id"] = rec["doc_id"]
    batch.append(rec)

if batch:
    stubs.insert_many(batch, ordered=False)

print(f"Total stubs uploaded: {stubs.count_documents({})}")
client.close()
print("Done.")