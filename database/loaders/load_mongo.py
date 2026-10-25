import os
import pandas as pd
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

df = pd.read_csv("data/SeoulBikeData.csv", encoding="latin1")
df.columns = [
    "date", "rented_bike_count", "hour", "temperature_c", "humidity_pct",
    "wind_speed_ms", "visibility_10m", "dew_point_c", "solar_radiation",
    "rainfall_mm", "snowfall_cm", "season", "holiday", "functioning_day",
]
df["timestamp"] = pd.to_datetime(df["date"], format="%d/%m/%Y") + pd.to_timedelta(df["hour"], unit="h")

docs = []
for _, r in df.iterrows():
    docs.append({
        "timestamp": r["timestamp"].to_pydatetime(),  
        "rented_bike_count": int(r["rented_bike_count"]),
        "season": r["season"],
        "holiday": r["holiday"],
        "functioning_day": r["functioning_day"],
        "weather": {
            "temperature_c": float(r["temperature_c"]),
            "humidity_pct": int(r["humidity_pct"]),
            "wind_speed_ms": float(r["wind_speed_ms"]),
            "visibility_10m": int(r["visibility_10m"]),
            "dew_point_c": float(r["dew_point_c"]),
            "solar_radiation": float(r["solar_radiation"]),
            "rainfall_mm": float(r["rainfall_mm"]),
            "snowfall_cm": float(r["snowfall_cm"]),
        },
    })

client = MongoClient(os.getenv("MONGO_URI"))
col = client[os.getenv("MONGO_DB")]["bike_records"]
col.drop()                      
col.insert_many(docs)
col.create_index([("timestamp", ASCENDING)], unique=True)
print("Inserted:", col.count_documents({}))