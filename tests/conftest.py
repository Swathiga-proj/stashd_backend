import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── 1. Set env var BEFORE importing app ──────────────────────────────────────
import os
os.environ["DATABASE_URL"] = "postgresql://postgres:poql@localhost:5432/stashd_test"

# ── 2. Now safe to import app ─────────────────────────────────────────────────
from app.main import app
from app.database import get_db, Base

# ── 3. Test engine & session factory ─────────────────────────────────────────
TEST_DATABASE_URL = "postgresql://postgres:poql@localhost:5432/stashd_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── 4. Create / drop tables once per session ─────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    print("\n>>> DROPPING ALL TABLES <<<")
    Base.metadata.drop_all(bind=engine) 
    print(">>> CREATING ALL TABLES <<<")  
    Base.metadata.create_all(bind=engine)
    yield
    print(">>> CLEANUP: DROPPING ALL TABLES <<<")
    Base.metadata.drop_all(bind=engine)


# ── 5. Per-test DB session with rollback for isolation ───────────────────────
@pytest.fixture(scope="session")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()   # ← undo every write after each test
    connection.close()


# ── 6. Override get_db so TestClient hits the test DB ────────────────────────
@pytest.fixture(scope="session", autouse=True)
def override_get_db(db_session):
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


# ── 7. Auth client (session-scoped, one signup/login for the whole suite) ────
@pytest.fixture(scope="session")
def auth_client(initialize_test_database):
    unique_id = str(uuid.uuid4())[:6]
    dynamic_phone = f"+918778{unique_id}"

    user_payload = {
        "name": "Priya Sharma",
        "phone_number": dynamic_phone,
        "password": "demo123",
        "confirm_password": "demo123",
    }

    with TestClient(app) as client:
        client.post("/auth/signup", json=user_payload)

        login_response = client.post("/auth/login", json={
            "phone_number": user_payload["phone_number"],
            "password": user_payload["password"],
        })
        token = login_response.json()["data"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})

        yield client