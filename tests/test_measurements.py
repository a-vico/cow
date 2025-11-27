from fastapi import status


class TestMeasurementsCreate:
    """Test cases for creating measurements"""

    def test_create_measurement(self, client):
        """Test creating a new measurement"""
        # First create a cow and sensor
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        cow_data = {"name": "Bessie", "birthdate": "2020-01-09"}
        sensor_id = "b3fd06f1-ce63-4897-97de-675badbf4076"
        sensor_data = {"unit": "L"}
        client.post(f"/api/v1/cows/{cow_id}", json=cow_data)
        client.post(f"/api/v1/sensors/{sensor_id}", json=sensor_data)

        measurement_data = {
            "sensor_id": sensor_id,
            "cow_id": cow_id,
            "timestamp": 1594462000.0,
            "value": 549.95,
        }
        response = client.post("/api/v1/measurements/", json=measurement_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["sensor_id"] == measurement_data["sensor_id"]
        assert data["cow_id"] == measurement_data["cow_id"]
        assert data["timestamp"] == "2020-07-11T10:06:40Z"
        assert data["value"] == measurement_data["value"]
        assert "id" in data
        assert "created_at" in data

    def test_create_measurement_invalid_sensor(self, client):
        """Test creating a measurement with non-existent sensor"""
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        cow_data = {"name": "Bessie", "birthdate": "2020-01-09"}
        client.post(f"/api/v1/cows/{cow_id}", json=cow_data)

        measurement_data = {
            "sensor_id": "00000000-0000-0000-0000-000000000000",
            "cow_id": cow_id,
            "timestamp": 1594462000.0,
            "value": 549.95,
        }
        response = client.post("/api/v1/measurements/", json=measurement_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_measurement_invalid_cow(self, client):
        """Test creating a measurement with non-existent cow"""
        sensor_data = {
            "id": "b3fd06f1-ce63-4897-97de-675badbf4076",
            "unit": "L",
        }
        client.post("/api/v1/sensors/", json=sensor_data)

        measurement_data = {
            "sensor_id": sensor_data["id"],
            "cow_id": "00000000-0000-0000-0000-000000000000",
            "timestamp": 1594462000.0,
            "value": 549.95,
        }
        response = client.post("/api/v1/measurements/", json=measurement_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_measurement_null_value(self, client):
        """Test creating a measurement with null value"""
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        client.post(
            f"/api/v1/cows/{cow_id}", json={"name": "Bessie", "birthdate": "2020-01-09"}
        )
        sensor_id = "b3fd06f1-ce63-4897-97de-675badbf4076"
        client.post(f"/api/v1/sensors/{sensor_id}", json={"unit": "L"})

        measurement = {
            "sensor_id": sensor_id,
            "cow_id": cow_id,
            "timestamp": 1609459200.0,
            "value": None,
        }

        response = client.post("/api/v1/measurements/", json=measurement)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_valid"] is False
        assert data["validation_error"] == "value is null"

    def test_create_measurement_minus_one_error(self, client):
        """Test creating a measurement with negative value"""
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        sensor_id = "b3fd06f1-ce63-4897-97de-675badbf4076"

        client.post(
            f"/api/v1/cows/{cow_id}", json={"name": "Bessie", "birthdate": "2020-01-09"}
        )
        client.post(f"/api/v1/sensors/{sensor_id}", json={"unit": "L"})

        measurement = {
            "sensor_id": sensor_id,
            "cow_id": cow_id,
            "timestamp": 1609459200.0,
            "value": -1,
        }

        response = client.post("/api/v1/measurements/", json=measurement)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_valid"] is False
        assert data["validation_error"] == "value is -1.0"

    def test_create_measurement_zero_error(self, client):
        """Test creating a measurement with zero value"""
        cow_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        sensor_id = "b3fd06f1-ce63-4897-97de-675badbf4076"

        client.post(
            f"/api/v1/cows/{cow_id}", json={"name": "Bessie", "birthdate": "2020-01-09"}
        )
        client.post(f"/api/v1/sensors/{sensor_id}", json={"unit": "L"})

        measurement = {
            "sensor_id": sensor_id,
            "cow_id": cow_id,
            "timestamp": 1609459200.0,
            "value": 0,
        }

        response = client.post("/api/v1/measurements/", json=measurement)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_valid"] is False
        assert data["validation_error"] == "value is 0.0"


class TestMeasurementsList:
    """Test cases for listing measurements"""

    def test_list_measurements_empty(self, client):
        """Test listing measurements when database is empty"""
        response = client.get("/api/v1/measurements/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["measurements"] == []
        assert data["total"] == 0

    def test_list_measurements_with_filters(self, client):
        """Test listing measurements with filters"""
        # Create test data
        cow1_id = "c821a6b7-8dd0-4b4e-9835-1c0c57264ba4"
        cow2_id = "71122813-53a2-4a95-bc73-4a5725ab2d41"
        cow1_data = {"name": "Bessie", "birthdate": "2020-01-09"}
        cow2_data = {"name": "Daisy", "birthdate": "2019-09-09"}
        sensor_data = {"id": "b3fd06f1-ce63-4897-97de-675badbf4076", "unit": "L"}

        client.post(f"/api/v1/cows/{cow1_id}", json=cow1_data)
        client.post(f"/api/v1/cows/{cow2_id}", json=cow2_data)
        client.post(
            f"/api/v1/sensors/{sensor_data['id'] if 'id' in sensor_data else 'b3fd06f1-ce63-4897-97de-675badbf4076'}",
            json=sensor_data,
        )

        # Create measurements for both cows
        client.post(
            "/api/v1/measurements/",
            json={
                "sensor_id": sensor_data["id"] if "id" in sensor_data else sensor_id,
                "cow_id": cow1_id,
                "timestamp": 1594462000.0,
                "value": 100.0,
            },
        )
        client.post(
            "/api/v1/measurements/",
            json={
                "sensor_id": sensor_data["id"] if "id" in sensor_data else sensor_id,
                "cow_id": cow2_id,
                "timestamp": 1594462100.0,
                "value": 200.0,
            },
        )

        # Filter by cow_id
        response = client.get(f"/api/v1/measurements/?cow_id={cow1_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["measurements"]) == 1
        assert data["measurements"][0]["cow_id"] == cow1_id
