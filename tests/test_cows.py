from datetime import date

from fastapi import status

from app import models
from app.routes.cows import get_latest_measurements


class TestCowsCreate:
    """Test cases for creating cows"""

    def test_create_cow(self, client):
        """Test creating a new cow"""
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        cow_data = {"name": "Bessie", "birthdate": "2020-01-09"}
        response = client.post(f"/api/v1/cows/{cow_id}", json=cow_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == cow_id
        assert data["name"] == cow_data["name"]
        assert data["birthdate"] == cow_data["birthdate"]
        assert "created_at" in data

    def test_create_cow_duplicate_id(self, client):
        """Test creating a cow with duplicate ID"""
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        cow_data = {"name": "Bessie", "birthdate": "2020-01-09"}
        client.post(f"/api/v1/cows/{cow_id}", json=cow_data)
        response = client.post(f"/api/v1/cows/{cow_id}", json=cow_data)
        assert response.status_code == status.HTTP_409_CONFLICT


class TestCowsList:
    """Test cases for listing cows"""

    def test_list_cows_empty(self, client):
        """Test listing cows when database is empty"""
        response = client.get("/api/v1/cows/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cows"] == []
        assert data["total"] == 0

    def test_list_cows(self, client):
        """Test listing cows"""
        cows = [
            (
                "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4",
                {"name": "Bessie", "birthdate": "2020-01-09"},
            ),
            (
                "71122813-53a2-4a95-bc73-4a5725ab2d41",
                {"name": "Daisy", "birthdate": "2019-09-09"},
            ),
        ]
        for cow_id, cow_data in cows:
            client.post(f"/api/v1/cows/{cow_id}", json=cow_data)

        response = client.get("/api/v1/cows/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["cows"]) == 2
        assert data["total"] == 2


class TestCowsGet:
    """Test cases for getting a specific cow"""

    def test_get_cow(self, client):
        """Test getting an existing cow"""
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        cow_data = {"name": "Bessie", "birthdate": "2020-01-09"}
        client.post(f"/api/v1/cows/{cow_id}", json=cow_data)

        response = client.get(f"/api/v1/cows/{cow_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == cow_id
        assert data["name"] == cow_data["name"]

    def test_get_cow_not_found(self, client):
        """Test getting a non-existent cow"""
        response = client.get("/api/v1/cows/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_cow_latest_measurements(self, client):
        """Test that get_cow returns the latest measurement per unit"""
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        cow_data = {"name": "Bessie", "birthdate": "2020-01-09"}
        client.post(f"/api/v1/cows/{cow_id}", json=cow_data)

        # create two sensors with different units
        sensor_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        sensor_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        client.post(f"/api/v1/sensors/{sensor_a}", json={"unit": "L"})
        client.post(f"/api/v1/sensors/{sensor_b}", json={"unit": "kg"})

        # For unit L: create two measurements, later one should be returned
        client.post(
            "/api/v1/measurements/",
            json={
                "sensor_id": sensor_a,
                "cow_id": cow_id,
                "timestamp": 1609459200.0,
                "value": 10.0,
            },
        )
        client.post(
            "/api/v1/measurements/",
            json={
                "sensor_id": sensor_a,
                "cow_id": cow_id,
                "timestamp": 1609459300.0,
                "value": 12.0,
            },
        )

        # For unit kg: create one measurement
        client.post(
            "/api/v1/measurements/",
            json={
                "sensor_id": sensor_b,
                "cow_id": cow_id,
                "timestamp": 1609459250.0,
                "value": 200.0,
            },
        )

        response = client.get(f"/api/v1/cows/{cow_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "latest_measurements" in data
        lm = data["latest_measurements"]
        # Should have the latest for L and the one for kg => 2 items
        assert isinstance(lm, list)
        assert len(lm) == 2
        # verify values: L -> 12.0, kg -> 200.0 (order not guaranteed)
        values = sorted([m["value"] for m in lm])
        assert values == [12.0, 200.0]
        # verify units present
        units = sorted([m["unit"] for m in lm])
        assert units == ["L", "kg"]


def test_get_latest_measurements_direct(db_session):
    # create cow
    cow = models.Cow(
        id="c821a6b7-8dd0-4b4e-9835-1c0c57264ba4",
        name="Bessie",
        birthdate=date(2020, 1, 9),
    )
    db_session.add(cow)

    # create sensors
    sensor_a = models.Sensor(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", unit="L")
    sensor_b = models.Sensor(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", unit="kg")
    db_session.add_all([sensor_a, sensor_b])
    db_session.commit()

    # add measurements for sensor_a (two timestamps) and sensor_b
    m1 = models.Measurement(
        sensor_id=sensor_a.id, cow_id=cow.id, timestamp=1609459200.0, value=10.0
    )
    m2 = models.Measurement(
        sensor_id=sensor_a.id, cow_id=cow.id, timestamp=1609459300.0, value=12.0
    )
    m3 = models.Measurement(
        sensor_id=sensor_b.id, cow_id=cow.id, timestamp=1609459250.0, value=200.0
    )
    db_session.add_all([m1, m2, m3])
    db_session.commit()

    latest = get_latest_measurements(db_session, cow.id)

    assert isinstance(latest, list)
    assert len(latest) == 2
    values = sorted([m.value for m in latest])
    assert values == [12.0, 200.0]
    units = sorted([getattr(m, "unit") for m in latest])
    assert units == ["L", "kg"]


class TestCowsDelete:
    """Test cases for deleting cows"""

    def test_delete_cow(self, client):
        """Test deleting an existing cow"""
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        cow_data = {"name": "Bessie", "birthdate": "2020-01-09"}
        client.post(f"/api/v1/cows/{cow_id}", json=cow_data)

        response = client.delete(f"/api/v1/cows/{cow_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify cow is deleted
        get_response = client.get(f"/api/v1/cows/{cow_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
