
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Response, status
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.database.mongodb_db import database
from app.schemas import BikeRecord

router = APIRouter(
    prefix="/api/mongo/bikes",
    tags=["MongoDB Bike Records"],
)

collection = database["bike_records"]

# Prevent multiple records from having the same timestamp.
collection.create_index(
    [("timestamp", ASCENDING)],
    unique=True,
)


def record_to_dict(document: dict) -> dict:
    """Convert a MongoDB document into an API response."""
    weather = document.get("weather", {})

    return {
        "id": str(document["_id"]),
        "timestamp": document["timestamp"].isoformat(),
        "rented_bike_count": document["rented_bike_count"],
        "temperature_c": weather.get("temperature_c"),
        "humidity_pct": weather.get("humidity_pct"),
        "wind_speed_ms": weather.get("wind_speed_ms"),
        "visibility_10m": weather.get("visibility_10m"),
        "dew_point_c": weather.get("dew_point_c"),
        "solar_radiation": weather.get("solar_radiation"),
        "rainfall_mm": weather.get("rainfall_mm"),
        "snowfall_cm": weather.get("snowfall_cm"),
        "season": document["season"],
        "holiday": document["holiday"],
        "functioning_day": document["functioning_day"],
    }


def to_document(record: BikeRecord) -> dict:
    """Convert a validated API record into the MongoDB document format."""
    data = record.model_dump()

    timestamp = data.pop("timestamp")
    season = data.pop("season")
    holiday = data.pop("holiday")
    functioning_day = data.pop("functioning_day")
    rented_bike_count = data.pop("rented_bike_count")

    return {
        "timestamp": timestamp,
        "rented_bike_count": rented_bike_count,
        "season": season,
        "holiday": holiday,
        "functioning_day": functioning_day,
        "weather": data,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_record(record: BikeRecord):
    document = to_document(record)

    try:
        result = collection.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A bike record with this timestamp already exists.",
        ) from exc

    saved = collection.find_one({"_id": result.inserted_id})
    return record_to_dict(saved)


@router.get("")
def get_records():
    documents = collection.find().sort("timestamp", DESCENDING)
    return [record_to_dict(doc) for doc in documents]


@router.get("/latest")
def get_latest_record():
    document = collection.find_one(
        sort=[("timestamp", DESCENDING)]
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No MongoDB bike records found.",
        )

    return record_to_dict(document)


@router.get("/range")
def get_records_by_date_range(
    start: datetime = Query(...),
    end: datetime = Query(...),
):
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start must be before or equal to end.",
        )

    documents = collection.find(
        {
            "timestamp": {
                "$gte": start,
                "$lte": end,
            }
        }
    ).sort("timestamp", ASCENDING)

    return [record_to_dict(doc) for doc in documents]


@router.get("/{record_id}")
def get_record(record_id: str):
    if not ObjectId.is_valid(record_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MongoDB record ID.",
        )

    document = collection.find_one({"_id": ObjectId(record_id)})

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MongoDB bike record not found.",
        )

    return record_to_dict(document)


@router.put("/{record_id}")
def update_record(record_id: str, record: BikeRecord):
    if not ObjectId.is_valid(record_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MongoDB record ID.",
        )

    try:
        updated = collection.find_one_and_update(
            {"_id": ObjectId(record_id)},
            {"$set": to_document(record)},
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A bike record with this timestamp already exists.",
        ) from exc

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MongoDB bike record not found.",
        )

    return record_to_dict(updated)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_record(record_id: str):
    if not ObjectId.is_valid(record_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MongoDB record ID.",
        )

    result = collection.delete_one({"_id": ObjectId(record_id)})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MongoDB bike record not found.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
