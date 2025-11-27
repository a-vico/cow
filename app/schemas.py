from datetime import date, datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer


# Cow Schemas
class CowBase(BaseModel):
    """Base schema for Cow"""

    name: str = Field(..., min_length=1, max_length=255)
    birthdate: date


class CowCreate(CowBase):
    """Schema for creating a cow"""


class CowResponse(CowBase):
    """Schema for cow response"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    latest_measurements: list["MeasurementResponse"] = []


class CowListResponse(BaseModel):
    """Schema for list of cows response"""

    cows: list[CowResponse]
    total: int


# Sensor Schemas
class SensorBase(BaseModel):
    """Base schema for Sensor"""

    unit: str = Field(..., min_length=1, max_length=10)


class SensorCreate(SensorBase):
    """Schema for creating a sensor"""


class SensorResponse(SensorBase):
    """Schema for sensor response"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class SensorListResponse(BaseModel):
    """Schema for list of sensors response"""

    sensors: list[SensorResponse]
    total: int


# Measurement Schemas
class MeasurementBase(BaseModel):
    """Base schema for Measurement"""

    sensor_id: str = Field(..., min_length=36, max_length=36)
    cow_id: str = Field(..., min_length=36, max_length=36)
    timestamp: float = Field(..., gt=0)
    value: float | None = None


class MeasurementCreate(MeasurementBase):
    """Schema for creating a measurement"""

    pass


class MeasurementResponse(MeasurementBase):
    """Schema for measurement response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    is_valid: bool
    validation_error: str | None = None
    unit: str | None = None
    timestamp: datetime

    @field_serializer("timestamp")
    def _serialize_timestamp(self, v):
        if isinstance(v, datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            # return ISO8601 string in UTC with 'Z' suffix
            s = v.astimezone(timezone.utc).isoformat()
            if s.endswith("+00:00"):
                s = s.replace("+00:00", "Z")
            return s
        return v


class MeasurementListResponse(BaseModel):
    """Schema for list of measurements response"""

    measurements: list[MeasurementResponse]
    total: int
