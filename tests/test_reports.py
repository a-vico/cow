import csv
from datetime import date, datetime

from app.database import get_db
from app.main import app


class FakeRow:
    def __init__(self, mapping: dict):
        self._mapping = mapping


class FakeResult(list):
    """Simple list-like result where iteration yields FakeRow"""

    def __iter__(self):
        for item in super().__iter__():
            yield FakeRow(item)


class FakeDB:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, sql, params=None):
        return FakeResult(self._rows)


def _override_db_with_rows(rows):
    fake_db = FakeDB(rows)

    def _get_db():
        try:
            yield fake_db
        finally:
            pass

    return _get_db


def test_weights_report_empty(client, db_session):
    # Insert a cow in real DB so code that lists cows (if used) still can work elsewhere
    from app.models import Cow

    cow = Cow(id="cow-1", name="Bessie", birthdate=date(2020, 1, 1))
    db_session.add(cow)
    db_session.commit()

    # Fake DB returns a single row indicating no data
    rows = [
        {
            "id": "cow-1",
            "name": "Bessie",
            "last_measured_at": None,
            "last_weight": None,
            "previous_30_day_weight_avg": None,
            "data_status": "No Data",
        }
    ]

    prev = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_db_with_rows(rows)

    resp = client.get("/api/v1/reports/weights")

    # restore
    if prev is not None:
        app.dependency_overrides[get_db] = prev
    else:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    content = resp.text
    assert "id" in content.splitlines()[0]
    assert "cow-1" in content


def test_weights_report_with_measurement(client, db_session):
    from app.models import Cow, Measurement, Sensor

    cow = Cow(id="cow-2", name="Molly", birthdate=date(2021, 6, 1))
    sensor = Sensor(id="s-kg", unit="kg")
    db_session.add_all([cow, sensor])
    db_session.commit()

    # Prepare fake result row
    rows = [
        {
            "id": "cow-2",
            "name": "Molly",
            "last_measured_at": "2023-01-10T12:00:00",
            "last_weight": 420.5,
            "previous_30_day_weight_avg": 415.0,
            "data_status": "Active",
        }
    ]

    prev = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_db_with_rows(rows)

    resp = client.get("/api/v1/reports/weights?date=2023-01-11")

    # restore
    if prev is not None:
        app.dependency_overrides[get_db] = prev
    else:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    text = resp.text
    assert "last_weight" in text.splitlines()[0]
    assert "Molly" in text


def test_milk_report_range(client, db_session):
    from app.models import Cow, Measurement, Sensor

    cow1 = Cow(id="cow-m1", name="Daisy", birthdate=date(2019, 5, 1))
    cow2 = Cow(id="cow-m2", name="Buttercup", birthdate=date(2018, 7, 2))
    sensor = Sensor(id="s-l", unit="L")
    db_session.add_all([cow1, cow2, sensor])
    db_session.commit()

    rows = [
        {"id": "cow-m1", "day": "2021-09-05", "milk_production": 12.0},
    ]

    prev = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_db_with_rows(rows)

    resp = client.get("/api/v1/reports/milk?start_date=2021-09-01&end_date=2021-09-10")

    # restore
    if prev is not None:
        app.dependency_overrides[get_db] = prev
    else:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    text = resp.text
    lines = text.splitlines()
    assert "milk_production" in lines[0]
    assert any("cow-m1" in ln for ln in lines[1:])
