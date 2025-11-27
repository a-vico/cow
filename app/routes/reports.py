import csv
import io
from datetime import date as _date
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import Date as _SQLDate
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()


@router.get("/weights")
async def weights_report(
    date: str | None = None, db: Session | AsyncSession = Depends(get_db)
):
    """Return current weights and average of last 30 days for every cow report as CSV for given date (YYYY-MM-DD). Defaults to today."""
    # parse date param
    report_date = date
    if report_date:
        try:
            rd = datetime.fromisoformat(date).date()
        except Exception:
            raise HTTPException(
                status_code=400, detail="Invalid date format, expected YYYY-MM-DD"
            )
    else:
        rd = _date.today()

    sql = text(
        """
WITH variables AS (
    SELECT :report_date as report_date
),
cow_weight AS (
    SELECT 
        m.cow_id,
        m.value,
        m.timestamp,
        ROW_NUMBER() OVER(PARTITION BY m.cow_id ORDER BY m.timestamp DESC) as rn,
        AVG(m.value) OVER(
            PARTITION BY m.cow_id 
            ORDER BY m.timestamp 
            RANGE BETWEEN INTERVAL '30 days' PRECEDING AND CURRENT ROW
        ) as previous_30_day_weight_avg
    FROM measurements m
    JOIN sensors s ON m.sensor_id = s.id
    CROSS JOIN variables v
    WHERE m.is_valid 
    AND s.unit = 'kg'
    AND m.timestamp <= v.report_date
)
SELECT 
    c.id, 
    c.name,
    cs.timestamp AS last_measured_at,
    cs.value AS last_weight,
    cs.previous_30_day_weight_avg,
    CASE 
        WHEN cs.value IS NULL THEN 'No Data'
        WHEN cs.timestamp < (v.report_date - INTERVAL '3 days') THEN 'Stale Data (>3 days)'
        ELSE 'Active'
    END as data_status,
    -- Potentially Ill Logic: Is current weight < 90% of the average?
    CASE 
        WHEN cs.value IS NULL OR cs.previous_30_day_weight_avg IS NULL THEN false 
        WHEN cs.value < (cs.previous_30_day_weight_avg * 0.95) THEN true 
        ELSE false 
    END as potentially_ill
FROM cows c
CROSS JOIN variables v
LEFT JOIN cow_weight cs ON c.id = cs.cow_id AND cs.rn = 1
ORDER BY c.name;
        """
    )

    # Bind the report_date as a SQL Date parameter and execute
    sql = sql.bindparams(bindparam("report_date", type_=_SQLDate))
    if isinstance(db, AsyncSession):
        result = await db.execute(sql, {"report_date": rd})
    else:
        result = db.execute(sql, {"report_date": rd})

    # Stream result as CSV
    output = io.StringIO()
    writer = None
    for row in result:
        if writer is None:
            writer = csv.writer(output)
            writer.writerow(row._mapping.keys())
        writer.writerow([row._mapping[k] for k in row._mapping.keys()])

    output.seek(0)
    headers = {
        "Content-Disposition": f"attachment; filename=report_weights_{rd.strftime('%Y%m%d')}.csv"
    }
    return StreamingResponse(
        io.StringIO(output.getvalue()), media_type="text/csv", headers=headers
    )


@router.get("/milk")
async def milk_report(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session | AsyncSession = Depends(get_db),
):
    """Return daily milk production per cow report as CSV between start_date and end_date (YYYY-MM-DD)."""
    # parse date params or use defaults from original SQL
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date).date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    else:
        sd = datetime.fromisoformat("1900-01-01").date()

    if end_date:
        try:
            ed = datetime.fromisoformat(end_date).date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    else:
        ed = datetime.fromisoformat("9999-12-31").date()

    sql = text(
        """
WITH variables AS (
    SELECT :start_date as start_date, :end_date as end_date
)
SELECT 
    c.id,
    m.timestamp::DATE as day,
    sum(m.value) as milk_production
FROM cows c
LEFT JOIN measurements m
ON c.id = m.cow_id
JOIN sensors s ON m.sensor_id = s.id
CROSS JOIN variables v
WHERE m.is_valid 
AND s.unit = 'L'
AND m.timestamp between v.start_date and v.end_date
GROUP BY 1,2
ORDER BY 1 desc, 2 desc
        """
    )

    sql = sql.bindparams(
        bindparam("start_date", type_=_SQLDate), bindparam("end_date", type_=_SQLDate)
    )
    if isinstance(db, AsyncSession):
        result = await db.execute(sql, {"start_date": sd, "end_date": ed})
    else:
        result = db.execute(sql, {"start_date": sd, "end_date": ed})

    # Stream result as CSV
    output = io.StringIO()
    writer = None
    for row in result:
        if writer is None:
            writer = csv.writer(output)
            writer.writerow(row._mapping.keys())
        writer.writerow([row._mapping[k] for k in row._mapping.keys()])

    output.seek(0)
    headers = {
        "Content-Disposition": f"attachment; filename=report_milk_{sd.strftime('%Y%m%d')}_{ed.strftime('%Y%m%d')}.csv"
    }
    return StreamingResponse(
        io.StringIO(output.getvalue()), media_type="text/csv", headers=headers
    )
