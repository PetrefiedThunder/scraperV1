"""
API integration tests.

Tests authentication, job creation, and basic API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from grandma_scraper.api.main import create_app
from grandma_scraper.db.base import Base
from grandma_scraper.db.session import get_db


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create app
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    # Create client
    with TestClient(app) as test_client:
        yield test_client

    # Drop tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(client):
    """Create a test user."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
    }

    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201

    return user_data


@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token."""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"],
    }

    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200

    token_data = response.json()
    return token_data["access_token"]


class TestHealth:
    """Health endpoint tests."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestAuthentication:
    """Authentication tests."""

    def test_register_user(self, client):
        """Test user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "password123",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registering with duplicate email fails."""
        response = client.post("/api/v1/auth/register", json=test_user)
        assert response.status_code == 400

    def test_login(self, client, test_user):
        """Test user login."""
        login_data = {
            "username": test_user["email"],
            "password": test_user["password"],
        }

        response = client.post("/api/v1/auth/token", data=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password fails."""
        login_data = {
            "username": test_user["email"],
            "password": "wrongpassword",
        }

        response = client.post("/api/v1/auth/token", data=login_data)
        assert response.status_code == 401


class TestUsers:
    """User endpoint tests."""

    def test_get_current_user(self, client, auth_token, test_user):
        """Test getting current user info."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/users/me", headers=headers)

        assert response.status_code == 200

        data = response.json()
        assert data["email"] == test_user["email"]

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without token fails."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestJobs:
    """Job endpoint tests."""

    def test_create_job(self, client, auth_token):
        """Test creating a scraping job."""
        job_data = {
            "name": "Test Job",
            "description": "A test scraping job",
            "enabled": True,
            "config": {
                "name": "Test Scraper",
                "start_url": "https://example.com",
                "item_selector": ".item",
                "fields": [
                    {
                        "name": "title",
                        "selector": ".title",
                        "attribute": "text",
                    }
                ],
            },
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/v1/jobs/", json=job_data, headers=headers)

        assert response.status_code == 201

        data = response.json()
        assert data["name"] == job_data["name"]
        assert "id" in data

    def test_list_jobs(self, client, auth_token):
        """Test listing user's jobs."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/jobs/", headers=headers)

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_job_invalid_config(self, client, auth_token):
        """Test creating job with invalid config fails."""
        job_data = {
            "name": "Invalid Job",
            "config": {
                "invalid": "config",
            },
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/v1/jobs/", json=job_data, headers=headers)

        assert response.status_code == 400
