
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.mysql_db import Base


class Season(Base):
    __tablename__ = "seasons"

    season_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    season_name: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    rentals: Mapped[list["BikeRental"]] = relationship(
        back_populates="season",
    )


class BikeRental(Base):
    __tablename__ = "bike_rentals"

    rental_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    timestamp: Mapped[DateTime] = mapped_column(
        DateTime,
        unique=True,
        nullable=False,
    )

    rented_bike_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    season_id: Mapped[int] = mapped_column(
        ForeignKey("seasons.season_id"),
        nullable=False,
    )

    holiday: Mapped[str] = mapped_column(
        Enum("Holiday", "No Holiday"),
        nullable=False,
    )

    functioning_day: Mapped[str] = mapped_column(
        Enum("Yes", "No"),
        nullable=False,
    )

    season: Mapped["Season"] = relationship(
        back_populates="rentals",
    )

    weather: Mapped["WeatherReading"] = relationship(
        back_populates="rental",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )


class WeatherReading(Base):
    __tablename__ = "weather_readings"

    weather_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    rental_id: Mapped[int] = mapped_column(
        ForeignKey(
            "bike_rentals.rental_id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
    )

    temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    humidity_pct: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    wind_speed_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    visibility_10m: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    dew_point_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    solar_radiation: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rainfall_mm: Mapped[float | None] = mapped_column(
    Float,
        nullable=True,
    )

    snowfall_cm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rental: Mapped["BikeRental"] = relationship(
        back_populates="weather",
    )
