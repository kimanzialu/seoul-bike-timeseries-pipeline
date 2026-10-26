
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Season = Literal["Winter", "Spring", "Summer", "Autumn"]

Holiday = Literal["Holiday", "No Holiday"]

FunctioningDay = Literal["Yes", "No"]


class BikeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Date and time of the bike rental record
    timestamp: datetime

    # Target variable
    rented_bike_count: int = Field(ge=0)

    # Weather information
    temperature_c: float | None = None

    humidity_pct: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    wind_speed_ms: float | None = Field(
        default=None,
        ge=0,
    )

    visibility_10m: int | None = Field(
        default=None,
        ge=0,
    )

    dew_point_c: float | None = None

    solar_radiation: float | None = Field(
        default=None,
        ge=0,
    )

    rainfall_mm: float | None = Field(
        default=None,
        ge=0,
    )

    snowfall_cm: float | None = Field(
        default=None,
        ge=0,
    )

    # Categorical information
    season: Season

    holiday: Holiday

    functioning_day: FunctioningDay
