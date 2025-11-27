from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter()


@router.post(
    "/{sensor_id}",
    response_model=schemas.SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sensor(
    sensor_id: str,
    sensor: schemas.SensorCreate,
    db: Session | AsyncSession = Depends(get_db),
):
    """Create a new sensor"""
    # Check if sensor with this ID already exists
    if isinstance(db, AsyncSession):
        res = await db.execute(
            select(models.Sensor).filter(models.Sensor.id == sensor_id)
        )
        existing_sensor = res.scalars().first()
    else:
        existing_sensor = (
            db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
        )
    if existing_sensor:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sensor with id {sensor_id} already exists",
        )

    data = sensor.model_dump()
    data["id"] = sensor_id
    db_sensor = models.Sensor(**data)
    db.add(db_sensor)
    if isinstance(db, AsyncSession):
        await db.commit()
        await db.refresh(db_sensor)
    else:
        db.commit()
        db.refresh(db_sensor)
    return db_sensor


@router.get("/", response_model=schemas.SensorListResponse)
async def list_sensors(
    skip: int = 0,
    limit: int = 100,
    db: Session | AsyncSession = Depends(get_db),
):
    """List all sensors with pagination"""
    if isinstance(db, AsyncSession):
        res = await db.execute(select(models.Sensor).offset(skip).limit(limit))
        sensors = res.scalars().all()
        total_res = await db.execute(select(func.count()).select_from(models.Sensor))
        total = total_res.scalar_one()
    else:
        sensors = db.query(models.Sensor).offset(skip).limit(limit).all()
        total = db.query(models.Sensor).count()
    return {"sensors": sensors, "total": total}


@router.get("/{sensor_id}", response_model=schemas.SensorResponse)
async def get_sensor(
    sensor_id: str,
    db: Session | AsyncSession = Depends(get_db),
):
    """Get a specific sensor by ID"""
    if isinstance(db, AsyncSession):
        res = await db.execute(
            select(models.Sensor).filter(models.Sensor.id == sensor_id)
        )
        sensor = res.scalars().first()
    else:
        sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found",
        )
    return sensor


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sensor(
    sensor_id: str,
    db: Session | AsyncSession = Depends(get_db),
):
    """Delete a sensor"""
    if isinstance(db, AsyncSession):
        res = await db.execute(
            select(models.Sensor).filter(models.Sensor.id == sensor_id)
        )
        db_sensor = res.scalars().first()
    else:
        db_sensor = (
            db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
        )
    if not db_sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with id {sensor_id} not found",
        )

    db.delete(db_sensor)
    db.commit()
    return None
