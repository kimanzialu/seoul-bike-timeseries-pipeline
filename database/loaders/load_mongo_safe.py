import os
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

load_dotenv()

mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_db = os.getenv("MONGO_DB", "seoul_bike")

client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
client.admin.command("ping")

database = client[mongo_db]
collection = database["bike_records"]

existing_count = collection.count_documents({})

if existing_count > 0:
    raise SystemExit(
        f"Stopped safely: bike_records already contains "
        f"{existing_count} documents. No data was changed."
    )

df = pd.read_csv("data/SeoulBikeData.csv", encoding="latin1")
df.columns = [
    "date", "rented_bike_count", "hour", "temperature_c", "humidity_pct",
    "wind_speed_ms", "visibility_10m", "dew_point_c", "solar_radiation",
    "rainfall_mm", "snowfall_cm", "season", "holiday", "functioning_day",
]

df["timestamp"] = (
    pd.to_datetime(df["date"], format="%d/%m/%Y")
    + pd.to_timedelta(df["hour"], unit="h")
)

documents = []

for _, row in df.iterrows():
    documents.append({
        "timestamp": row["timestamp"].to_pydatetime(),
        "rented_bike_count": int(row["rented_bike_count"]),
        "season": row["season"],
        "holiday": row["holiday"],
        "functioning_day": row["functioning_day"],
        "weather": {
            "temperature_c": float(row["temperature_c"]),
            "humidity_pct": int(row["humidity_pct"]),
            "wind_speed_ms": float(row["wind_speed_ms"]),
            "visibility_10m": int(row["visibility_10m"]),
            "dew_point_c": float(row["dew_point_c"]),
            "solar_radiation": float(row["solar_radiation"]),
            "rainfall_mm": float(row["rainfall_mm"]),
            "snowfall_cm": float(row["snowfall_cm"]),
        },
    })

collection.create_index([("timestamp", ASCENDING)], unique=True)
result = collection.insert_many(documents)

print("Inserted documents:", len(result.inserted_ids))
print("Total documents now:", collection.count_documents({}))

client.close()
