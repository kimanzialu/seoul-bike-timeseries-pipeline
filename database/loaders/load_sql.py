import os
from urllib.parse import quote_plus
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

#Read and clean the CSV
df = pd.read_csv("data/SeoulBikeData.csv", encoding="latin1")
df.columns = [
    "date", "rented_bike_count", "hour", "temperature_c", "humidity_pct",
    "wind_speed_ms", "visibility_10m", "dew_point_c", "solar_radiation",
    "rainfall_mm", "snowfall_cm", "season", "holiday", "functioning_day",
]
df["timestamp"] = pd.to_datetime(df["date"], format="%d/%m/%Y") + pd.to_timedelta(df["hour"], unit="h")

# Database Connection
user = os.getenv("MYSQL_USER")
password = quote_plus(os.getenv("MYSQL_PASSWORD"))
host = os.getenv("MYSQL_HOST")
port = os.getenv("MYSQL_PORT")
db = os.getenv("MYSQL_DB")
engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}")

# Here tables are emptied so the script can be re-run safely
with engine.begin() as conn:
    conn.execute(text("DELETE FROM weather_readings"))
    conn.execute(text("DELETE FROM bike_rentals"))
    conn.execute(text("DELETE FROM seasons"))


pd.DataFrame({"season_name": df["season"].unique()}).to_sql(
    "seasons", engine, if_exists="append", index=False)
season_map = pd.read_sql("SELECT season_id, season_name FROM seasons", engine)
season_map = dict(zip(season_map.season_name, season_map.season_id))

rentals = df[["timestamp", "rented_bike_count", "holiday", "functioning_day"]].copy()
rentals["season_id"] = df["season"].map(season_map)
rentals.to_sql("bike_rentals", engine, if_exists="append", index=False)

ids = pd.read_sql("SELECT rental_id, timestamp FROM bike_rentals", engine)
weather = df[["timestamp", "temperature_c", "humidity_pct", "wind_speed_ms",
              "visibility_10m", "dew_point_c", "solar_radiation",
              "rainfall_mm", "snowfall_cm"]].merge(ids, on="timestamp")
weather = weather.drop(columns="timestamp")
weather.to_sql("weather_readings", engine, if_exists="append", index=False)

print("Loaded rows:", len(rentals), len(weather))