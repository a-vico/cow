from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_measurement(
    measurement: schemas.MeasurementCreate,
    db: Session | AsyncSession = Depends(get_db),
):
    """Create a new measurement"""
    # Validate that sensor exists
    # Support both sync and async DB sessions
    if isinstance(db, AsyncSession):
        res = await db.execute(
            select(models.Sensor).filter(models.Sensor.id == measurement.sensor_id)
        )
        sensor = res.scalars().first()
    else:
        sensor = (
            db.query(models.Sensor)
            .filter(models.Sensor.id == measurement.sensor_id)
            .first()
        )
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {measurement.sensor_id} not found",
        )

    # Validate that cow exists
    if isinstance(db, AsyncSession):
        res = await db.execute(
            select(models.Cow).filter(models.Cow.id == measurement.cow_id)
        )
        cow = res.scalars().first()
    else:
        cow = db.query(models.Cow).filter(models.Cow.id == measurement.cow_id).first()
    if not cow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cow with id {measurement.cow_id} not found",
        )

    # Prepare DB measurement dict
    mdata = measurement.model_dump()

    # Convert epoch float timestamp (seconds) to timezone-aware datetime (UTC)
    ts = mdata.get("timestamp")
    try:
        mdata["timestamp"] = datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timestamp"
        )

    # Validate value based on sensor unit
    unit = sensor.unit
    validation_error = None
    is_valid = True

    value = mdata.get("value")
    if value is None:
        validation_error = "value is null"
        is_valid = False
    else:
        if unit in ("L", "kg"):
            if value <= 0:
                validation_error = f"value is {value}"
                is_valid = False

    mdata["is_valid"] = is_valid
    mdata["validation_error"] = validation_error

    db_measurement = models.Measurement(**mdata)
    db.add(db_measurement)
    if isinstance(db, AsyncSession):
        await db.commit()
        await db.refresh(db_measurement)
    else:
        db.commit()
        db.refresh(db_measurement)

    return db_measurement


@router.get("/", response_model=schemas.MeasurementListResponse)
async def list_measurements(
    skip: int = 0,
    limit: int = 100,
    cow_id: str = None,
    sensor_id: str = None,
    db: Session | AsyncSession = Depends(get_db),
):
    """List all measurements with pagination and optional filters"""
    if isinstance(db, AsyncSession):
        stmt = select(models.Measurement)
        if cow_id:
            stmt = stmt.filter(models.Measurement.cow_id == cow_id)
        if sensor_id:
            stmt = stmt.filter(models.Measurement.sensor_id == sensor_id)
        stmt = stmt.offset(skip).limit(limit)
        res = await db.execute(stmt)
        measurements = res.scalars().all()

        # total count
        count_stmt = select(func.count()).select_from(models.Measurement)
        if cow_id:
            count_stmt = count_stmt.filter(models.Measurement.cow_id == cow_id)
        if sensor_id:
            count_stmt = count_stmt.filter(models.Measurement.sensor_id == sensor_id)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()
    else:
        query = db.query(models.Measurement)
        if cow_id:
            query = query.filter(models.Measurement.cow_id == cow_id)
        if sensor_id:
            query = query.filter(models.Measurement.sensor_id == sensor_id)
        measurements = query.offset(skip).limit(limit).all()
        total = query.count()

    return {"measurements": measurements, "total": total}


@router.get("/{measurement_id}", response_model=schemas.MeasurementResponse)
async def get_measurement(
    measurement_id: int,
    db: Session | AsyncSession = Depends(get_db),
):
    """Get a specific measurement by ID"""
    if isinstance(db, AsyncSession):
        res = await db.execute(
            select(models.Measurement).filter(models.Measurement.id == measurement_id)
        )
        measurement = res.scalars().first()
    else:
        measurement = (
            db.query(models.Measurement)
            .filter(models.Measurement.id == measurement_id)
            .first()
        )
    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurement with id {measurement_id} not found",
        )
    return measurement


@router.delete("/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_measurement(
    measurement_id: int,
    db: Session | AsyncSession = Depends(get_db),
):
    """Delete a measurement"""
    if isinstance(db, AsyncSession):
        res = await db.execute(
            select(models.Measurement).filter(models.Measurement.id == measurement_id)
        )
        db_measurement = res.scalars().first()
    else:
        db_measurement = (
            db.query(models.Measurement)
            .filter(models.Measurement.id == measurement_id)
            .first()
        )
    if not db_measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurement with id {measurement_id} not found",
        )

    db.delete(db_measurement)
    if isinstance(db, AsyncSession):
        await db.commit()
    else:
        db.commit()
    return None
