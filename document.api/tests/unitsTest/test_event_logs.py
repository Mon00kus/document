import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import EventLog, Base
from datetime import datetime

# Usamos SQLite en memoria para pruebas
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    """Crea la BD en memoria y carga datos de prueba antes de cada test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(EventLog(event_type="ANALYSIS", description="normal1", created_at=datetime(2025, 12, 17, 9, 18)))
    db.add(EventLog(event_type="ANALYSIS", description="normal2", created_at=datetime(2025, 12, 18, 20, 52)))
    db.commit()
    yield
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_export_event_logs_success():
    response = client.get(
        "/api/v1/event-logs/export?event_type=ANALYSIS&start_date=2025-12-17&end_date=2025-12-18"
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )
    # Validamos que el contenido exportado incluya al menos uno de los registros
    assert b"normal1" in response.content or b"normal2" in response.content

def test_export_event_logs_invalid_range():
    response = client.get(
        "/api/v1/event-logs/export?start_date=2025-12-18&end_date=2025-12-17"
    )
    assert response.status_code == 400
    assert "no puede ser posterior" in response.text