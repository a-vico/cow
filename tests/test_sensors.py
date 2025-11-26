from fastapi import status


class TestSensorsCreate:
    """Test cases for creating sensors"""

    def test_create_sensor(self, client):
        """Test creating a new sensor"""
        sensor_id = "b3fd06f1-ce63-4897-97de-675badbf4076"
        sensor_data = {"unit": "L"}
        response = client.post(f"/api/v1/sensors/{sensor_id}", json=sensor_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == sensor_id
        assert data["unit"] == sensor_data["unit"]
        assert "created_at" in data

    def test_create_sensor_duplicate_id(self, client):
        """Test creating a sensor with duplicate ID"""
        sensor_id = "b3fd06f1-ce63-4897-97de-675badbf4076"
        sensor_data = {"unit": "L"}
        client.post(f"/api/v1/sensors/{sensor_id}", json=sensor_data)
        response = client.post(f"/api/v1/sensors/{sensor_id}", json=sensor_data)
        assert response.status_code == status.HTTP_409_CONFLICT


class TestSensorsList:
    """Test cases for listing sensors"""

    def test_list_sensors_empty(self, client):
        """Test listing sensors when database is empty"""
        response = client.get("/api/v1/sensors/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sensors"] == []
        assert data["total"] == 0

    def test_list_sensors(self, client):
        """Test listing sensors"""
        sensors = [
            ("b3fd06f1-ce63-4897-97de-675badbf4076", {"unit": "L"}),
            ("64183e73-b494-42d1-9f7c-c344003f3205", {"unit": "kg"}),
        ]
        for sensor_id, sensor_data in sensors:
            client.post(f"/api/v1/sensors/{sensor_id}", json=sensor_data)

        response = client.get("/api/v1/sensors/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sensors"]) == 2
        assert data["total"] == 2
