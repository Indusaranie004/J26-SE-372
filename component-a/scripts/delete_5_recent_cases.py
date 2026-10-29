from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["lk_legal"]

# Delete 5 recent 2025-2026 cases
cases_to_delete = list(db["cases"].find(
    {"date": {"$gte": "2025"}},
    {"_id": 1}
).limit(5))

ids = [c["_id"] for c in cases_to_delete]
print("Deleting:", ids)
db["cases"].delete_many({"_id": {"$in": ids}})
print("Deleted 5 cases from MongoDB")