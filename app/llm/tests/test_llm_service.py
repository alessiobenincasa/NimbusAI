import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import uuid

from llm_service import LLMService
from models import Brand, Product, ProductAttribute

class TestLLMService(unittest.TestCase):
    def setUp(self):
        # Create LLM service instance
        self.llm_service = LLMService()
        
        # Mock database session
        self.mock_db = MagicMock()
        
        # Setup mock data
        self.brand_id = str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        
        # Mock brand
        self.mock_brand = MagicMock(spec=Brand)
        self.mock_brand.id = uuid.UUID(self.brand_id)
        self.mock_brand.name = "Test Brand"
        self.mock_brand.description = "Test Brand Description"
        
        # Mock product
        self.mock_product = MagicMock(spec=Product)
        self.mock_product.id = uuid.uuid4()
        self.mock_product.name = "Test Product"
        self.mock_product.description = "Test Product Description"
        self.mock_product.price = 99.99
        
        # Mock product attributes
        self.mock_attribute = MagicMock(spec=ProductAttribute)
        self.mock_attribute.name = "Color"
        self.mock_attribute.value = "Red"
        
        # Configure product to have attributes
        self.mock_product.attributes = [self.mock_attribute]
    
    @patch('llm_service.LLMService.is_model_loaded')
    @patch('llm_service.LLMService.load_model')
    async def test_generate_without_model_loaded(self, mock_load_model, mock_is_model_loaded):
        """Test generate method when model is not loaded"""
        # Configure mocks
        mock_is_model_loaded.return_value = False
        mock_load_model.return_value = None
        
        # Call method
        response = await self.llm_service.generate(
            brand_info={"brand_name": "Test"},
            user_message="Hello",
            conversation_history=""
        )
        
        # Check response
        self.assertIn("initializing", response)
        mock_load_model.assert_called_once()
    
    @patch('llm_service.LLMService.is_model_loaded')
    async def test_get_brand_info(self, mock_is_model_loaded):
        """Test get_brand_info method"""
        # Configure mocks
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_brand
        self.mock_db.query.return_value.filter.return_value.all.return_value = [self.mock_product]
        
        # Mock the query for product attributes
        attribute_query_mock = MagicMock()
        attribute_query_mock.filter.return_value.all.return_value = [self.mock_attribute]
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=self.mock_brand)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[self.mock_product])))),
            attribute_query_mock
        ]
        
        # Call method
        result = await self.llm_service.get_brand_info(self.brand_id, self.mock_db)
        
        # Check result
        self.assertEqual(result["brand_name"], "Test Brand")
        self.assertEqual(result["brand_description"], "Test Brand Description")
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["name"], "Test Product")
        self.assertIn("attributes", result["products"][0])
    
    @patch('llm_service.LLMService.is_model_loaded')
    async def test_get_conversation_history(self, mock_is_model_loaded):
        """Test get_conversation_history method"""
        # Mock messages
        mock_user_message = MagicMock()
        mock_user_message.sender = "user"
        mock_user_message.content = "Hello"
        
        mock_ai_message = MagicMock()
        mock_ai_message.sender = "ai"
        mock_ai_message.content = "Hi there!"
        
        # Configure mock
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_user_message, mock_ai_message
        ]
        
        # Call method
        result = await self.llm_service.get_conversation_history(self.conversation_id, self.mock_db)
        
        # Check result
        self.assertIn("Human: Hello", result)
        self.assertIn("AI Assistant: Hi there!", result)
    
    @patch('llm_service.LLMService.is_model_loaded')
    @patch('llm_service.LLMChain')
    async def test_generate_with_model_loaded(self, mock_chain, mock_is_model_loaded):
        """Test generate method when model is loaded"""
        # Configure mocks
        mock_is_model_loaded.return_value = True
        
        # Setup chain mock
        self.llm_service.chain = MagicMock()
        self.llm_service.chain.run.return_value = "This is a test response"
        
        # Prepare data
        brand_info = {
            "brand_name": "Test Brand",
            "brand_description": "Test Description",
            "products": [
                {
                    "name": "Product",
                    "description": "Description",
                    "price": 99.99,
                    "attributes": {"Color": "Red"}
                }
            ]
        }
        
        # Call method
        response = await self.llm_service.generate(
            brand_info=brand_info,
            user_message="Tell me about your products",
            conversation_history="Human: Hi\nAI Assistant: Hello"
        )
        
        # Check response
        self.assertEqual(response, "This is a test response")
        self.llm_service.chain.run.assert_called_once()
    
    def test_memory_usage(self):
        """Test get_memory_usage method"""
        # Call method
        result = self.llm_service.get_memory_usage()
        
        # Check result structure
        self.assertIn("rss", result)
        self.assertIn("vms", result)
        self.assertIn("percent", result)

if __name__ == "__main__":
    unittest.main() 