import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime
import uuid

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import Brand, Product, Conversation, Message
from database import get_db

class TestAPI(unittest.TestCase):
    def setUp(self):
        # Create a test client
        self.client = TestClient(app)
        
        # Create mock DB session
        self.mock_db = MagicMock(spec=Session)
        
        # Setup mock data
        self.mock_brand = Brand(
            id=uuid.uuid4(),
            name="Test Brand",
            description="Test Brand Description"
        )
        
        self.mock_product = Product(
            id=uuid.uuid4(),
            brand_id=self.mock_brand.id,
            name="Test Product",
            description="Test Product Description",
            price=99.99
        )

        # Create a sample conversation with realistic data
        self.mock_conversation = Conversation(
            id=uuid.uuid4(),
            brand_id=self.mock_brand.id,
            session_id="test_session",
            created_at=datetime.now()
        )
        
        # Override the get_db dependency
        def override_get_db():
            return self.mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
    def tearDown(self):
        # Remove the override
        app.dependency_overrides = {}
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})
    
    def test_get_brands(self):
        """Test get brands endpoint"""
        # Setup mock
        self.mock_db.query.return_value.all.return_value = [self.mock_brand]
        
        # Call API
        response = self.client.get("/brands")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Test Brand")
    
    def test_get_brand(self):
        """Test get brand by ID endpoint"""
        # Setup mock
        brand_id = str(self.mock_brand.id)
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_brand
        
        # Call API
        response = self.client.get(f"/brands/{brand_id}")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Brand")
    
    def test_get_products(self):
        """Test get products by brand ID endpoint"""
        # Setup mock
        brand_id = str(self.mock_brand.id)
        self.mock_db.query.return_value.filter.return_value.all.return_value = [self.mock_product]
        
        # Call API
        response = self.client.get(f"/brands/{brand_id}/products")
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Test Product")
    
    def test_create_conversation(self):
        """Test create conversation endpoint"""
        # Setup mocks
        brand_id = str(self.mock_brand.id)
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_brand
        
        # Mock du résultat de la création de conversation
        def mock_add(obj):
            # Simuler l'attribution d'un ID et d'une date lors de l'ajout en base
            obj.id = uuid.uuid4()
            obj.created_at = datetime.now()
            obj.messages = []
            return None
            
        self.mock_db.add.side_effect = mock_add
        
        # Call API
        response = self.client.post(f"/brands/{brand_id}/conversations")
        
        # Check that conversation was created
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.mock_db.add.called)
        self.assertTrue(self.mock_db.commit.called)
    
    @patch('httpx.AsyncClient.post')
    def test_create_message(self, mock_httpx):
        """Test create message endpoint"""
        # Setup mocks
        conversation_id = str(uuid.uuid4())
        mock_conversation = MagicMock(
            id=uuid.UUID(conversation_id),
            brand_id=self.mock_brand.id
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        # Configure mock response from LLM service
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Test AI response"}
        mock_httpx.return_value = mock_response
        
        # Simulating message creation
        def mock_add(obj):
            if isinstance(obj, Message):
                obj.id = uuid.uuid4()
                obj.created_at = datetime.now()
            return None
            
        self.mock_db.add.side_effect = mock_add
        
        # Call API
        response = self.client.post(
            f"/conversations/{conversation_id}/messages",
            json={"content": "Hello"}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.mock_db.add.called)
        self.assertTrue(self.mock_db.commit.called)
        # Check that we saved both messages (user + AI)
        self.assertEqual(self.mock_db.add.call_count, 2)

if __name__ == "__main__":
    unittest.main() 