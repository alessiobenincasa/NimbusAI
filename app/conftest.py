import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)
sys.path.insert(0, os.path.join(app_dir, 'api'))
sys.path.insert(0, os.path.join(app_dir, 'llm'))

# Override DATABASE_URL for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Monkey patch the database modules to use SQLite for tests
@pytest.fixture(autouse=True)
def mock_db_connection(monkeypatch):
    """Replace the real database with a SQLite in-memory DB for tests"""
    # Create in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Mock the get_db function
    def mock_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Apply the patch to both API and LLM modules
    try:
        from api.database import get_db as api_get_db
        monkeypatch.setattr("api.database.get_db", mock_get_db)
    except ImportError:
        pass
        
    try:
        from llm.database import get_db as llm_get_db
        monkeypatch.setattr("llm.database.get_db", mock_get_db)
    except ImportError:
        pass 