"""
Test fixtures: run the real FastAPI app (Task 3) against in-memory databases.

MySQL is swapped for SQLite and MongoDB for mongomock, so the Task 4 pipeline
can be tested end to end, through the actual API routes, without either
server running.
"""
import mongomock
import pymongo
import pytest

# Must happen before the app is imported: mongo_bikes.py connects at import time.
pymongo.MongoClient = mongomock.MongoClient

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.database.mongodb_db as mongodb_db  # noqa: E402
from app.database.mysql_db import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.models import BikeRental, Season, WeatherReading  # noqa: E402
from app.routes import bikes as sql_routes  # noqa: E402
from app.routes import mongo_bikes  # noqa: E402
from forecasting.preprocessing import load_raw_csv  # noqa: E402
from forecasting.train_model import DEFAULT_CSV, DEFAULT_MODEL  # noqa: E402

WEATHER = ["temperature_c", "humidity_pct", "wind_speed_ms", "visibility_10m",
           "dew_point_c", "solar_radiation", "rainfall_mm", "snowfall_cm"]
N_DAYS = 21  # the last three weeks of the dataset is enough history for every test


@pytest.fixture(scope="session")
def dataset():
    return load_raw_csv(DEFAULT_CSV)


@pytest.fixture(scope="session")
def model_path():
    if not DEFAULT_MODEL.is_file():
        pytest.skip("Model missing: run `python -m forecasting.train_model` first.")
    return DEFAULT_MODEL


@pytest.fixture()
def api(dataset):
    """A TestClient on the real app, with both databases loaded with the same rows."""
    rows = dataset.tail(N_DAYS * 24)

    engine = create_engine("sqlite://", poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    with Session() as db:
        seasons = {name: Season(season_name=name) for name in rows["season"].unique()}
        db.add_all(seasons.values())
        for r in rows.itertuples():
            rental = BikeRental(timestamp=r.timestamp.to_pydatetime(),
                                rented_bike_count=int(r.rented_bike_count),
                                season=seasons[r.season], holiday=r.holiday,
                                functioning_day=r.functioning_day)
            rental.weather = WeatherReading(**{c: getattr(r, c) for c in WEATHER})
            db.add(rental)
        db.commit()

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[sql_routes.get_db] = override_get_db

    collection = mongo_bikes.collection
    collection.delete_many({})
    collection.insert_many([{
        "timestamp": r.timestamp.to_pydatetime(),
        "rented_bike_count": int(r.rented_bike_count),
        "season": r.season, "holiday": r.holiday, "functioning_day": r.functioning_day,
        "weather": {c: float(getattr(r, c)) for c in WEATHER},
    } for r in rows.itertuples()])

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    collection.delete_many({})
    engine.dispose()
