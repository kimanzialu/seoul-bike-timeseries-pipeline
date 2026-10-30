from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database.mysql_db import SessionLocal
from app.models import BikeRental, Season, WeatherReading
from app.schemas import BikeRecord

router = APIRouter(prefix="/api/bikes", tags=["Bike Records"])


def get_db():
    """Provide a database session for one request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def record_to_dict(rental: BikeRental) -> dict:
    """Convert a database rental into the API response format."""
    weather = rental.weather

    return {
        "id": rental.rental_id,
        "timestamp": rental.timestamp.isoformat(),
        "rented_bike_count": rental.rented_bike_count,
        "temperature_c": weather.temperature_c if weather else None,
        "humidity_pct": weather.humidity_pct if weather else None,
        "wind_speed_ms": weather.wind_speed_ms if weather else None,
        "visibility_10m": weather.visibility_10m if weather else None,
        "dew_point_c": weather.dew_point_c if weather else None,
        "solar_radiation": weather.solar_radiation if weather else None,
        "rainfall_mm": weather.rainfall_mm if weather else None,
        "snowfall_cm": weather.snowfall_cm if weather else None,
        "season": rental.season.season_name,
        "holiday": rental.holiday,
        "functioning_day": rental.functioning_day,
    }


def get_rental_statement():
    """Load each rental together with its season and weather."""
    return select(BikeRental).options(
        joinedload(BikeRental.season),
        joinedload(BikeRental.weather),
    )


def get_or_create_season(db: Session, season_name: str) -> Season:
    """Find a season or create it if it does not exist."""
    season = db.scalar(
        select(Season).where(Season.season_name == season_name)
    )

    if season is None:
        season = Season(season_name=season_name)
        db.add(season)
        db.flush()

    return season


@router.post("", status_code=status.HTTP_201_CREATED)
def create_record(
    record: BikeRecord,
    db: Session = Depends(get_db),
):
    try:
        season = get_or_create_season(db, record.season)

        rental = BikeRental(
            timestamp=record.timestamp,
            rented_bike_count=record.rented_bike_count,
            season=season,
            holiday=record.holiday,
            functioning_day=record.functioning_day,
        )
        db.add(rental)
        db.flush()

        weather = WeatherReading(
            rental=rental,
            temperature_c=record.temperature_c,
            humidity_pct=record.humidity_pct,
            wind_speed_ms=record.wind_speed_ms,
            visibility_10m=record.visibility_10m,
            dew_point_c=record.dew_point_c,
            solar_radiation=record.solar_radiation,
            rainfall_mm=record.rainfall_mm,
            snowfall_cm=record.snowfall_cm,
        )
        db.add(weather)
        db.commit()

        db.refresh(rental)
        return record_to_dict(rental)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A bike record with this timestamp already exists.",
        ) from exc


@router.get("")
def get_records(db: Session = Depends(get_db)):
    statement = get_rental_statement().order_by(BikeRental.timestamp.desc())
    rentals = db.scalars(statement).unique().all()
    return [record_to_dict(rental) for rental in rentals]


@router.get("/latest")
def get_latest_record(db: Session = Depends(get_db)):
    statement = (
        get_rental_statement()
        .order_by(BikeRental.timestamp.desc())
        .limit(1)
    )
    rental = db.scalars(statement).unique().first()

    if rental is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No bike records found.",
        )

    return record_to_dict(rental)


@router.get("/range")
def get_records_by_date_range(
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: Session = Depends(get_db),
):
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start must be before or equal to end.",
        )

    statement = (
        get_rental_statement()
        .where(BikeRental.timestamp >= start)
        .where(BikeRental.timestamp <= end)
        .order_by(BikeRental.timestamp.asc())
    )
    rentals = db.scalars(statement).unique().all()
    return [record_to_dict(rental) for rental in rentals]


@router.get("/{record_id}")
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    statement = get_rental_statement().where(
        BikeRental.rental_id == record_id
    )
    rental = db.scalars(statement).unique().first()

    if rental is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bike record not found.",
        )

    return record_to_dict(rental)


@router.put("/{record_id}")
def update_record(
    record_id: int,
    record: BikeRecord,
    db: Session = Depends(get_db),
):
    rental = db.get(BikeRental, record_id)

    if rental is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bike record not found.",
        )

    try:
        rental.timestamp = record.timestamp
        rental.rented_bike_count = record.rented_bike_count
        rental.season = get_or_create_season(db, record.season)
        rental.holiday = record.holiday
        rental.functioning_day = record.functioning_day

        if rental.weather is None:
            rental.weather = WeatherReading()

        rental.weather.temperature_c = record.temperature_c
        rental.weather.humidity_pct = record.humidity_pct
        rental.weather.wind_speed_ms = record.wind_speed_ms
        rental.weather.visibility_10m = record.visibility_10m
        rental.weather.dew_point_c = record.dew_point_c
        rental.weather.solar_radiation = record.solar_radiation
        rental.weather.rainfall_mm = record.rainfall_mm
        rental.weather.snowfall_cm = record.snowfall_cm

        db.commit()

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A bike record with this timestamp already exists.",
        ) from exc

    statement = get_rental_statement().where(
        BikeRental.rental_id == record_id
    )
    updated = db.scalars(statement).unique().first()
    return record_to_dict(updated)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    rental = db.get(BikeRental, record_id)

    if rental is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bike record not found.",
        )

    db.delete(rental)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
