from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Cow(Base):
    """Model representing a cow"""

    __tablename__ = "cows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    birthdate: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement", back_populates="cow", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Cow(id={self.id}, name={self.name})>"


class Sensor(Base):
    """Model representing a sensor"""

    __tablename__ = "sensors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement", back_populates="sensor", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Sensor(id={self.id}, unit={self.unit})>"


class Measurement(Base):
    """Model representing a measurement from a sensor for a cow"""

    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sensors.id"), nullable=False, index=True
    )
    cow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cows.id"), nullable=False, index=True
    )
    timestamp: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=True)
    is_valid: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="true",
    )
    validation_error: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="measurements")
    cow: Mapped["Cow"] = relationship("Cow", back_populates="measurements")

    def __repr__(self) -> str:
        return f"<Measurement(id={self.id}, sensor_id={self.sensor_id}, cow_id={self.cow_id})>"
