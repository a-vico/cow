from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter()


@router.post(
    "/{cow_id}",
    response_model=schemas.CowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cow(
    cow_id: str,
    cow: schemas.CowCreate,
    db: Session = Depends(get_db),
):
    """Create a new cow"""
    # Check if cow with this ID already exists
    existing_cow = db.query(models.Cow).filter(models.Cow.id == cow_id).first()
    if existing_cow:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cow with id {cow_id} already exists",
        )

    data = cow.model_dump()
    data["id"] = cow_id
    db_cow = models.Cow(**data)
    db.add(db_cow)
    db.commit()
    db.refresh(db_cow)
    return db_cow


@router.get("/", response_model=schemas.CowListResponse)
async def list_cows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all cows with pagination"""
    cows = db.query(models.Cow).offset(skip).limit(limit).all()
    total = db.query(models.Cow).count()
    return {"cows": cows, "total": total}


@router.get("/{cow_id}", response_model=schemas.CowResponse)
async def get_cow(
    cow_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific cow by ID"""
    cow = db.query(models.Cow).filter(models.Cow.id == cow_id).first()
    if not cow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cow with id {cow_id} not found",
        )
    latest = get_latest_measurements(db, cow_id)
    setattr(cow, "latest_measurements", latest)
    return cow


def get_latest_measurements(db: Session, cow_id: str):
    """Return latest measurement per sensor unit for given cow_id.

    Uses DISTINCT ON when connected to PostgreSQL for a single-query optimized path,
    otherwise falls back to querying per unit.
    """
    latest = []
    try:
        bind = db.get_bind()
        dialect_name = getattr(bind.dialect, "name", None)
    except Exception:
        dialect_name = None

    if dialect_name and dialect_name.startswith("postgres"):
        rows = (
            db.query(models.Measurement, models.Sensor.unit)
            .join(models.Sensor, models.Measurement.sensor_id == models.Sensor.id)
            .filter(models.Measurement.cow_id == cow_id)
            .distinct(models.Sensor.unit)
            .order_by(models.Sensor.unit, models.Measurement.timestamp.desc())
            .all()
        )
        for m, unit in rows:
            setattr(m, "unit", unit)
            latest.append(m)
        return latest

    # fallback: collect units then pick latest per unit
    unit_rows = (
        db.query(models.Sensor.unit)
        .join(models.Measurement, models.Measurement.sensor_id == models.Sensor.id)
        .filter(models.Measurement.cow_id == cow_id)
        .distinct()
        .all()
    )

    for (unit,) in unit_rows:
        m = (
            db.query(models.Measurement)
            .join(models.Sensor, models.Measurement.sensor_id == models.Sensor.id)
            .filter(models.Measurement.cow_id == cow_id, models.Sensor.unit == unit)
            .order_by(models.Measurement.timestamp.desc())
            .first()
        )
        if m:
            setattr(m, "unit", unit)
            latest.append(m)

    return latest


@router.delete("/{cow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cow(
    cow_id: str,
    db: Session = Depends(get_db),
):
    """Delete a cow"""
    db_cow = db.query(models.Cow).filter(models.Cow.id == cow_id).first()
    if not db_cow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cow with id {cow_id} not found",
        )

    db.delete(db_cow)
    db.commit()
    return None
