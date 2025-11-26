from datetime import date

from fastapi import status


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
