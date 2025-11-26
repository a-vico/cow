from fastapi import APIRouter, Depends, HTTPException, status
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
    db: Session = Depends(get_db),
):
    """Create a new measurement"""
    # Validate that sensor exists
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
    cow = db.query(models.Cow).filter(models.Cow.id == measurement.cow_id).first()
    if not cow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cow with id {measurement.cow_id} not found",
        )

    db_measurement = models.Measurement(**measurement.model_dump())
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement


@router.get("/", response_model=schemas.MeasurementListResponse)
async def list_measurements(
    skip: int = 0,
    limit: int = 100,
    cow_id: str = None,
    sensor_id: str = None,
    db: Session = Depends(get_db),
):
    """List all measurements with pagination and optional filters"""
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
    db: Session = Depends(get_db),
):
    """Get a specific measurement by ID"""
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
    db: Session = Depends(get_db),
):
    """Delete a measurement"""
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
    db.commit()
    return None
