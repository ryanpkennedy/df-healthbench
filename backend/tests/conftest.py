"""
Pytest configuration and shared fixtures.

This module provides reusable fixtures for all test files, ensuring
consistent test setup, teardown, and isolation.

============================================================================
DATABASE STRATEGIES: SQLite vs PostgreSQL
============================================================================

This test suite supports TWO database strategies:

1. ⚡ SQLite (in-memory) - FAST
   - For: Unit tests, CRUD operations, API endpoints, business logic
   - Speed: Milliseconds
   - No dependencies: Runs without Docker
   - Fixtures: db_session, test_client, async_client
   - Limitations: No pgvector support

2. 🐘 PostgreSQL - PRODUCTION PARITY
   - For: Integration tests, RAG, embeddings, vector search
   - Speed: Seconds
   - Requires: Docker PostgreSQL with pgvector running
   - Fixtures: postgres_db_session, test_client_postgres, async_client_postgres
   - Benefits: Full pgvector support, production parity

============================================================================
FIXTURE SELECTION GUIDE
============================================================================

FAST UNIT TESTS (SQLite):
    - test_health_check(test_client)
    - test_create_document(db_session)
    - test_document_api(test_client, sample_document)

INTEGRATION TESTS (PostgreSQL):
    - test_vector_search(postgres_db_session)
    - test_rag_endpoint(test_client_postgres)
    - test_embeddings(async_client_postgres, sample_document_postgres)

RULE OF THUMB:
- If test needs pgvector/embeddings → Use postgres_* fixtures
- Otherwise → Use regular fixtures (faster)

============================================================================
"""

import sys
import pytest
import os
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
import httpx

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add backend directory to Python path so we can import app module
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.database import Base, get_db
from app.models.document import Document
from app.models.document_embedding import DocumentEmbedding
from app.models.document_summary import DocumentSummary
from app.schemas.document import DocumentCreate


# ============================================================================
# DATABASE FIXTURES - SQLite (Fast Unit Tests)
# ============================================================================

@pytest.fixture(scope="function")
def db_engine():
    """
    Create an in-memory SQLite database engine for testing.
    
    ⚡ FAST: Use for unit tests that don't need pgvector
    
    Uses StaticPool to maintain a single connection across the test,
    ensuring data persists within the test but is cleaned up after.
    
    Good for: CRUD operations, API endpoints, business logic
    NOT for: RAG tests, embeddings, vector search (needs PostgreSQL)
    """
    # Use in-memory SQLite for fast, isolated tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Create a SQLite database session for testing with automatic rollback.
    
    ⚡ FAST: Use for unit tests that don't need pgvector
    
    Each test gets a fresh session that rolls back all changes after
    the test completes, ensuring test isolation.
    
    Usage:
        def test_something(db_session):
            document = Document(title="Test", content="Content")
            db_session.add(document)
            db_session.commit()
            # Changes automatically rolled back after test
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ============================================================================
# DATABASE FIXTURES - PostgreSQL (Integration Tests with PGVector)
# ============================================================================

@pytest.fixture(scope="function")
def postgres_db_engine():
    """
    Create PostgreSQL database engine for integration tests.
    
    🐘 PRODUCTION PARITY: Use for integration tests requiring pgvector
    
    Connects to actual PostgreSQL database (requires Docker running).
    Uses TEST_DATABASE_URL env var if set, otherwise falls back to DATABASE_URL.
    
    Good for: RAG tests, embeddings, vector search, full integration tests
    Requires: PostgreSQL with pgvector extension running
    """
    # Get test database URL from env, or use default
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://dfuser:dfpassword@localhost:5432/df_healthbench"
    )
    
    # If TEST_DATABASE_URL not set, fall back to regular DATABASE_URL
    # (careful: this will use the dev database)
    if test_db_url == "postgresql://dfuser:dfpassword@localhost:5432/df_healthbench":
        # Try the regular DATABASE_URL if test DB doesn't exist
        dev_db_url = os.getenv("DATABASE_URL")
        if dev_db_url:
            test_db_url = dev_db_url
    
    try:
        engine = create_engine(test_db_url, pool_pre_ping=True)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        yield engine
        
        # Cleanup
        engine.dispose()
        
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.fixture(scope="function")
def postgres_db_session(postgres_db_engine) -> Generator[Session, None, None]:
    """
    Create a PostgreSQL database session for testing with automatic rollback.
    
    🐘 PRODUCTION PARITY: Use for integration tests requiring pgvector
    
    Each test gets a fresh session that rolls back all changes after
    the test completes, ensuring test isolation.
    
    Usage:
        @pytest.mark.integration
        def test_vector_search(postgres_db_session):
            # Can use pgvector features
            embedding = DocumentEmbedding(...)
            postgres_db_session.add(embedding)
            postgres_db_session.commit()
            # Changes automatically rolled back after test
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=postgres_db_engine
    )
    
    # Start a connection and transaction
    connection = postgres_db_engine.connect()
    transaction = connection.begin()
    
    # Create session bound to this connection
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()  # Rollback all changes
        connection.close()


@pytest.fixture(scope="function")
def clean_database(db_session):
    """
    Ensure SQLite database is clean before each test.
    
    ⚡ FAST: For SQLite tests
    
    Explicitly deletes all records from all tables. Use this when you need
    to guarantee a completely empty database state.
    
    Usage:
        def test_something(clean_database):
            # Database is guaranteed to be empty
            pass
    """
    # Delete all records in reverse order (respects foreign keys)
    db_session.query(DocumentEmbedding).delete()
    db_session.query(DocumentSummary).delete()
    db_session.query(Document).delete()
    db_session.commit()
    
    yield db_session
    
    # Cleanup after test
    db_session.query(DocumentEmbedding).delete()
    db_session.query(DocumentSummary).delete()
    db_session.query(Document).delete()
    db_session.commit()


@pytest.fixture(scope="function")
def clean_postgres_database(postgres_db_session):
    """
    Ensure PostgreSQL database is clean before each test.
    
    🐘 PRODUCTION PARITY: For PostgreSQL tests
    
    Explicitly deletes all records from all tables. Use this when you need
    to guarantee a completely empty database state.
    
    Usage:
        @pytest.mark.integration
        def test_something(clean_postgres_database):
            # Database is guaranteed to be empty
            pass
    """
    # Delete all records in reverse order (respects foreign keys)
    postgres_db_session.query(DocumentEmbedding).delete()
    postgres_db_session.query(DocumentSummary).delete()
    postgres_db_session.query(Document).delete()
    postgres_db_session.commit()
    
    yield postgres_db_session
    
    # Cleanup after test (transaction rollback will handle this automatically)
    postgres_db_session.query(DocumentEmbedding).delete()
    postgres_db_session.query(DocumentSummary).delete()
    postgres_db_session.query(Document).delete()
    postgres_db_session.commit()


# ============================================================================
# API CLIENT FIXTURES - SQLite
# ============================================================================

@pytest.fixture(scope="function")
def test_client(db_session) -> TestClient:
    """
    FastAPI TestClient with SQLite database.
    
    ⚡ FAST: Use for API tests that don't need pgvector
    
    This client uses the test SQLite session instead of the production
    database, ensuring tests don't affect real data.
    
    Good for: Health checks, document CRUD, LLM endpoints
    NOT for: RAG endpoints, embedding operations
    
    Usage:
        def test_endpoint(test_client):
            response = test_client.get("/health")
            assert response.status_code == 200
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client_postgres(postgres_db_session) -> TestClient:
    """
    FastAPI TestClient with PostgreSQL database.
    
    🐘 PRODUCTION PARITY: Use for API tests requiring pgvector
    
    This client uses the real PostgreSQL database, allowing tests
    to use pgvector features like embeddings and vector search.
    
    Good for: RAG endpoints, embedding operations, full integration tests
    Requires: PostgreSQL with pgvector running
    
    Usage:
        @pytest.mark.integration
        def test_rag_endpoint(test_client_postgres):
            response = test_client_postgres.post("/rag/answer_question", ...)
            assert response.status_code == 200
    """
    def override_get_db():
        try:
            yield postgres_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clear overrides
    app.dependency_overrides.clear()


# ============================================================================
# API CLIENT FIXTURES - Async (SQLite & PostgreSQL)
# ============================================================================

@pytest.fixture(scope="function")
async def async_client(db_session) -> httpx.AsyncClient:
    """
    httpx AsyncClient for testing async endpoints with SQLite.
    
    ⚡ FAST: Use for async API tests that don't need pgvector
    
    Use this for endpoints that require async operations.
    
    Good for: Async operations, LLM endpoints
    NOT for: RAG endpoints, embedding operations
    
    Usage:
        @pytest.mark.asyncio
        async def test_async_endpoint(async_client):
            response = await async_client.get("/health")
            assert response.status_code == 200
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use ASGITransport for testing FastAPI apps with httpx
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        timeout=30.0
    ) as client:
        yield client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client_postgres(postgres_db_session) -> httpx.AsyncClient:
    """
    httpx AsyncClient for testing async endpoints with PostgreSQL.
    
    🐘 PRODUCTION PARITY: Use for async API tests requiring pgvector
    
    Use this for async endpoints that require pgvector features
    like embeddings and vector search.
    
    Good for: RAG endpoints, embedding operations, full async integration tests
    Requires: PostgreSQL with pgvector running
    
    Usage:
        @pytest.mark.integration
        @pytest.mark.asyncio
        async def test_rag_async(async_client_postgres):
            response = await async_client_postgres.post("/rag/answer_question", ...)
            assert response.status_code == 200
    """
    def override_get_db():
        try:
            yield postgres_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use ASGITransport for testing FastAPI apps with httpx
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        timeout=120.0
    ) as client:
        yield client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def live_async_client() -> httpx.AsyncClient:
    """
    httpx AsyncClient for testing against a live running server.
    
    Use this for end-to-end tests that require a fully running server
    instance (e.g., testing containerized deployment).
    
    Requires: Server running on http://localhost:8000
    
    Usage:
        @pytest.mark.e2e
        @pytest.mark.asyncio
        async def test_live_endpoint(live_async_client):
            response = await live_async_client.get("/health")
            assert response.status_code == 200
    """
    async with httpx.AsyncClient(
        base_url="http://localhost:8000",
        timeout=120.0
    ) as client:
        yield client


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def sample_document(db_session) -> Document:
    """
    Create a sample document for testing with SQLite.
    
    ⚡ FAST: For SQLite tests
    
    Returns a committed Document instance that can be used across tests.
    
    Usage:
        def test_get_document(test_client, sample_document):
            response = test_client.get(f"/documents/{sample_document.id}")
            assert response.status_code == 200
    """
    document = Document(
        title="Test SOAP Note - Sample Patient",
        content="""Subjective: 
45-year-old male presents with persistent cough and mild fever for 3 days.
Patient reports fatigue and occasional shortness of breath.

Objective:
Temperature: 100.4°F
Blood Pressure: 128/82 mmHg
Heart Rate: 78 bpm
Respiratory Rate: 16/min
O2 Saturation: 96% on room air

Lung auscultation reveals scattered wheezes bilaterally.

Assessment:
1. Acute bronchitis
2. Mild respiratory distress

Plan:
1. Prescribe albuterol inhaler 2 puffs q4-6h PRN
2. Increase fluid intake
3. Rest and avoid strenuous activity
4. Follow-up in 7 days if symptoms persist
5. Return immediately if shortness of breath worsens"""
    )
    
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    return document


@pytest.fixture(scope="function")
def sample_document_postgres(postgres_db_session) -> Document:
    """
    Create a sample document for testing with PostgreSQL.
    
    🐘 PRODUCTION PARITY: For PostgreSQL tests
    
    Returns a committed Document instance that can be used across tests.
    Useful for RAG and embedding tests that need the actual database.
    
    Usage:
        @pytest.mark.integration
        def test_get_document(test_client_postgres, sample_document_postgres):
            response = test_client_postgres.get(f"/documents/{sample_document_postgres.id}")
            assert response.status_code == 200
    """
    document = Document(
        title="Test SOAP Note - Sample Patient",
        content="""Subjective: 
45-year-old male presents with persistent cough and mild fever for 3 days.
Patient reports fatigue and occasional shortness of breath.

Objective:
Temperature: 100.4°F
Blood Pressure: 128/82 mmHg
Heart Rate: 78 bpm
Respiratory Rate: 16/min
O2 Saturation: 96% on room air

Lung auscultation reveals scattered wheezes bilaterally.

Assessment:
1. Acute bronchitis
2. Mild respiratory distress

Plan:
1. Prescribe albuterol inhaler 2 puffs q4-6h PRN
2. Increase fluid intake
3. Rest and avoid strenuous activity
4. Follow-up in 7 days if symptoms persist
5. Return immediately if shortness of breath worsens"""
    )
    
    postgres_db_session.add(document)
    postgres_db_session.commit()
    postgres_db_session.refresh(document)
    
    return document


@pytest.fixture(scope="function")
def sample_document_with_diagnosis(db_session) -> Document:
    """
    Create a sample document with clear diagnoses for testing extraction (SQLite).
    
    ⚡ FAST: For SQLite tests
    
    Contains Type 2 Diabetes and Hypertension for ICD-10-CM code testing.
    
    Usage:
        def test_extraction(sample_document_with_diagnosis):
            # Document has clear diagnoses for extraction testing
            pass
    """
    document = Document(
        title="Test SOAP Note - Diabetes Patient",
        content="""Subjective:
62-year-old female with Type 2 Diabetes Mellitus presents for routine follow-up.
Reports compliance with Metformin 500mg twice daily.
Also has history of Hypertension, currently on Lisinopril 10mg daily.

Objective:
Temperature: 98.6°F
Blood Pressure: 138/86 mmHg
Heart Rate: 72 bpm
BMI: 32.4

Lab Results:
HbA1c: 7.2%
Fasting Glucose: 142 mg/dL

Assessment:
1. Type 2 Diabetes Mellitus - controlled
2. Essential Hypertension - controlled
3. Obesity

Plan:
1. Continue Metformin 500mg BID
2. Continue Lisinopril 10mg daily
3. Dietary counseling for weight management
4. Recheck HbA1c in 3 months"""
    )
    
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    
    return document


@pytest.fixture(scope="function")
def sample_document_with_diagnosis_postgres(postgres_db_session) -> Document:
    """
    Create a sample document with clear diagnoses for testing extraction (PostgreSQL).
    
    🐘 PRODUCTION PARITY: For PostgreSQL tests
    
    Contains Type 2 Diabetes and Hypertension for ICD-10-CM code testing.
    Useful for agent extraction and FHIR conversion integration tests.
    
    Usage:
        @pytest.mark.integration
        def test_extraction(sample_document_with_diagnosis_postgres):
            # Document has clear diagnoses for extraction testing
            pass
    """
    document = Document(
        title="Test SOAP Note - Diabetes Patient",
        content="""Subjective:
62-year-old female with Type 2 Diabetes Mellitus presents for routine follow-up.
Reports compliance with Metformin 500mg twice daily.
Also has history of Hypertension, currently on Lisinopril 10mg daily.

Objective:
Temperature: 98.6°F
Blood Pressure: 138/86 mmHg
Heart Rate: 72 bpm
BMI: 32.4

Lab Results:
HbA1c: 7.2%
Fasting Glucose: 142 mg/dL

Assessment:
1. Type 2 Diabetes Mellitus - controlled
2. Essential Hypertension - controlled
3. Obesity

Plan:
1. Continue Metformin 500mg BID
2. Continue Lisinopril 10mg daily
3. Dietary counseling for weight management
4. Recheck HbA1c in 3 months"""
    )
    
    postgres_db_session.add(document)
    postgres_db_session.commit()
    postgres_db_session.refresh(document)
    
    return document


@pytest.fixture(scope="session")
def sample_soap_note() -> str:
    """
    Load a real SOAP note from med_docs for testing.
    
    Returns the text content of soap_01.txt for use in tests.
    Session-scoped since file content doesn't change.
    
    Usage:
        def test_with_real_soap(sample_soap_note):
            assert len(sample_soap_note) > 0
            assert "Subjective:" in sample_soap_note
    """
    soap_file = Path(__file__).parent.parent.parent / "med_docs" / "soap" / "soap_01.txt"
    
    if not soap_file.exists():
        pytest.skip(f"SOAP file not found: {soap_file}")
    
    with open(soap_file, "r") as f:
        return f.read()


@pytest.fixture(scope="session")
def sample_soap_notes_dir() -> Path:
    """
    Get path to SOAP notes directory.
    
    Useful for tests that need to iterate over multiple SOAP notes.
    
    Usage:
        def test_all_soaps(sample_soap_notes_dir):
            soap_files = list(sample_soap_notes_dir.glob("*.txt"))
            assert len(soap_files) > 0
    """
    soap_dir = Path(__file__).parent.parent.parent / "med_docs" / "soap"
    
    if not soap_dir.exists():
        pytest.skip(f"SOAP directory not found: {soap_dir}")
    
    return soap_dir


@pytest.fixture(scope="function")
def sample_extraction_data():
    """
    Sample structured extraction data for FHIR conversion testing.
    
    Returns a StructuredClinicalData Pydantic model with
    ICD-10-CM and RxNorm codes.
    
    Usage:
        def test_fhir_conversion(sample_extraction_data):
            # Use pre-populated extraction data
            pass
    """
    from app.schemas.extraction import (
        StructuredClinicalData,
        PatientInfo,
        DiagnosisCode,
        MedicationCode,
        VitalSigns
    )
    
    return StructuredClinicalData(
        patient_info=PatientInfo(age="45", gender="male"),
        diagnoses=[
            DiagnosisCode(
                text="Type 2 Diabetes Mellitus",
                icd10_code="E11.9",
                icd10_description="Type 2 diabetes mellitus without complications",
                confidence="exact"
            ),
            DiagnosisCode(
                text="Essential Hypertension",
                icd10_code="I10",
                icd10_description="Essential (primary) hypertension",
                confidence="exact"
            )
        ],
        medications=[
            MedicationCode(
                text="Metformin 500mg",
                rxnorm_code="860975",
                rxnorm_name="Metformin 500 MG Oral Tablet",
                confidence="exact"
            ),
            MedicationCode(
                text="Lisinopril 10mg",
                rxnorm_code="314076",
                rxnorm_name="Lisinopril 10 MG Oral Tablet",
                confidence="exact"
            )
        ],
        vital_signs=VitalSigns(
            blood_pressure="138/86",
            heart_rate="72",
            temperature="98.6°F"
        ),
        lab_results=[
            "HbA1c: 7.2%",
            "Fasting Glucose: 142 mg/dL"
        ],
        plan_actions=[
            "Continue Metformin 500mg BID",
            "Continue Lisinopril 10mg daily",
            "Recheck HbA1c in 3 months"
        ]
    )


@pytest.fixture(scope="function")
def sample_extraction_data_dict() -> dict:
    """
    Sample structured extraction data as dictionary (for API endpoint testing).
    
    Returns a dictionary matching the FHIRConversionRequest schema.
    
    Usage:
        def test_api_endpoint(sample_extraction_data_dict):
            response = client.post("/fhir/convert", json=sample_extraction_data_dict)
    """
    return {
        "patient_info": {
            "age": "45",
            "gender": "male"
        },
        "diagnoses": [
            {
                "text": "Type 2 Diabetes Mellitus",
                "icd10_code": "E11.9",
                "icd10_description": "Type 2 diabetes mellitus without complications",
                "confidence": "exact"
            },
            {
                "text": "Essential Hypertension",
                "icd10_code": "I10",
                "icd10_description": "Essential (primary) hypertension",
                "confidence": "exact"
            }
        ],
        "medications": [
            {
                "text": "Metformin 500mg",
                "rxnorm_code": "860975",
                "rxnorm_name": "Metformin 500 MG Oral Tablet",
                "confidence": "exact"
            },
            {
                "text": "Lisinopril 10mg",
                "rxnorm_code": "314076",
                "rxnorm_name": "Lisinopril 10 MG Oral Tablet",
                "confidence": "exact"
            }
        ],
        "vital_signs": {
            "blood_pressure": "138/86",
            "heart_rate": "72",
            "temperature": "98.6°F"
        },
        "lab_results": [
            "HbA1c: 7.2%",
            "Fasting Glucose: 142 mg/dL"
        ],
        "plan_actions": [
            "Continue Metformin 500mg BID",
            "Continue Lisinopril 10mg daily",
            "Recheck HbA1c in 3 months"
        ]
    }


# ============================================================================
# MOCK DATA FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def mock_openai_response():
    """
    Mock OpenAI API response for testing without API calls.
    
    Returns a dictionary that mimics OpenAI's response structure.
    
    Usage:
        def test_with_mock_openai(mock_openai_response):
            # Use mock response instead of real API call
            pass
    """
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test summary of the medical note."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 50,
            "total_tokens": 200
        }
    }


@pytest.fixture(scope="function")
def mock_embedding_vector():
    """
    Mock embedding vector for testing without OpenAI API calls.
    
    Returns a 1536-dimension vector (matching text-embedding-3-small).
    
    Usage:
        def test_embedding(mock_embedding_vector):
            assert len(mock_embedding_vector) == 1536
    """
    import random
    random.seed(42)  # Deterministic for testing
    return [random.random() for _ in range(1536)]


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset singleton services between tests.
    
    This ensures that singleton instances (like LLMService) don't carry
    state between tests. Auto-used for all tests.
    """
    # Import singleton service modules
    from app.services import llm, agent_extraction, fhir_conversion
    
    # Reset singleton instances (use correct variable names)
    llm._llm_service_instance = None
    agent_extraction._extractor_service = None
    fhir_conversion._fhir_service_instance = None
    
    yield
    
    # Cleanup after test
    llm._llm_service_instance = None
    agent_extraction._extractor_service = None
    fhir_conversion._fhir_service_instance = None


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """
    Get path to test data directory.
    
    Useful for accessing test JSON files and other test assets.
    
    Usage:
        def test_with_file(test_data_dir):
            json_file = test_data_dir / "test_extraction_request.json"
            with open(json_file) as f:
                data = json.load(f)
    """
    return Path(__file__).parent


# ============================================================================
# PYTEST CONFIGURATION HOOKS
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers.
    
    This ensures all markers are registered and documented.
    """
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (requires DB and services)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (requires running server)"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (LLM calls, external APIs)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically.
    
    This adds the 'slow' marker to any test that has 'llm' or 'openai'
    in its name, ensuring developers don't forget to mark slow tests.
    """
    for item in items:
        # Auto-mark tests with 'llm' or 'openai' in name as slow
        if "llm" in item.nodeid.lower() or "openai" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
        
        # Auto-mark tests with 'api' in path as api tests
        if "api" in item.nodeid.lower() and "test_api" not in item.nodeid:
            if "endpoint" in item.name.lower() or "client" in str(item.fixturenames):
                item.add_marker(pytest.mark.api)

