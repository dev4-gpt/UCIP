"""AI assistant chatbot for planners and users."""
import os
from typing import Dict, List, Optional

from loguru import logger

from models.nlp.rag_engine import RAGEngine


class UCIPAssistant:
    """AI assistant for carbon intelligence queries."""

    def __init__(
        self,
        rag_engine: Optional[RAGEngine] = None,
        model: str = "gpt-4",
    ):
        """Initialize UCIP assistant.
        
        Args:
            rag_engine: RAG engine instance
            model: LLM model to use
        """
        self.rag = rag_engine or RAGEngine()
        self.model = model
        self.conversation_history = []
        
        logger.info("UCIP Assistant initialized")

    def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
    ) -> Dict:
        """Process a chat message.
        
        Args:
            message: User message
            context: Optional context (building_id, campus, etc.)
            
        Returns:
            Response dictionary
        """
        logger.info(f"User query: {message}")
        
        # Store message in history
        self.conversation_history.append({
            'role': 'user',
            'content': message
        })
        
        # Determine query type
        query_type = self._classify_query(message)
        
        # Route to appropriate handler
        if query_type == "policy":
            response = self._handle_policy_query(message)
        elif query_type == "emissions":
            response = self._handle_emissions_query(message, context)
        elif query_type == "hotspot":
            response = self._handle_hotspot_query(message, context)
        elif query_type == "forecast":
            response = self._handle_forecast_query(message, context)
        else:
            response = self._handle_general_query(message)
        
        # Store response in history
        self.conversation_history.append({
            'role': 'assistant',
            'content': response['answer']
        })
        
        return response

    def _classify_query(self, message: str) -> str:
        """Classify query type.
        
        Args:
            message: User message
            
        Returns:
            Query type
        """
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['policy', 'target', 'compliance', 'regulation']):
            return "policy"
        elif any(word in message_lower for word in ['emissions', 'carbon', 'co2', 'ghg']):
            return "emissions"
        elif any(word in message_lower for word in ['hotspot', 'problem', 'high', 'priority']):
            return "hotspot"
        elif any(word in message_lower for word in ['forecast', 'predict', 'future', 'trend']):
            return "forecast"
        else:
            return "general"

    def _handle_policy_query(self, message: str) -> Dict:
        """Handle policy-related queries.
        
        Args:
            message: User message
            
        Returns:
            Response dictionary
        """
        # Use RAG to retrieve relevant policy information
        result = self.rag.query(message, k=3)
        
        return {
            'answer': result['answer'],
            'sources': result['sources'],
            'confidence': result['confidence'],
            'type': 'policy'
        }

    def _handle_emissions_query(
        self,
        message: str,
        context: Optional[Dict] = None,
    ) -> Dict:
        """Handle emissions-related queries.
        
        Args:
            message: User message
            context: Optional context
            
        Returns:
            Response dictionary
        """
        # Placeholder - query emissions database
        answer = "Based on recent data, campus emissions are approximately 125,000 kg CO2 per day. " \
                "The largest contributors are building heating (45%), electricity (35%), and transportation (20%)."
        
        return {
            'answer': answer,
            'data': {
                'total_emissions': 125000,
                'breakdown': {
                    'heating': 56250,
                    'electricity': 43750,
                    'transportation': 25000
                }
            },
            'confidence': 0.9,
            'type': 'emissions'
        }

    def _handle_hotspot_query(
        self,
        message: str,
        context: Optional[Dict] = None,
    ) -> Dict:
        """Handle hotspot-related queries.
        
        Args:
            message: User message
            context: Optional context
            
        Returns:
            Response dictionary
        """
        answer = "I've identified 3 high-priority emissions hotspots on campus:\n\n" \
                "1. Pattee Library - 3,500 kg CO2/day (after-hours HVAC usage)\n" \
                "2. Thomas Building - 2,800 kg CO2/day (inefficient lighting)\n" \
                "3. Engineering Building - 2,600 kg CO2/day (lab equipment)\n\n" \
                "Recommended interventions could reduce emissions by 30-40%."
        
        return {
            'answer': answer,
            'hotspots': [
                {'building': 'Pattee Library', 'emissions': 3500, 'priority': 'high'},
                {'building': 'Thomas Building', 'emissions': 2800, 'priority': 'high'},
                {'building': 'Engineering Building', 'emissions': 2600, 'priority': 'high'}
            ],
            'confidence': 0.85,
            'type': 'hotspot'
        }

    def _handle_forecast_query(
        self,
        message: str,
        context: Optional[Dict] = None,
    ) -> Dict:
        """Handle forecast-related queries.
        
        Args:
            message: User message
            context: Optional context
            
        Returns:
            Response dictionary
        """
        answer = "Based on current trends and planned interventions, I forecast:\n\n" \
                "- 7-day outlook: Emissions will remain stable around 125,000 kg CO2/day\n" \
                "- 30-day outlook: Expected 5% reduction after HVAC schedule optimization\n" \
                "- 2030 target: On track to achieve 50% reduction with planned interventions"
        
        return {
            'answer': answer,
            'forecast': {
                '7_day': 125000,
                '30_day': 118750,
                '2030_target': 62500
            },
            'confidence': 0.75,
            'type': 'forecast'
        }

    def _handle_general_query(self, message: str) -> Dict:
        """Handle general queries.
        
        Args:
            message: User message
            
        Returns:
            Response dictionary
        """
        answer = "I'm the UCIP AI assistant. I can help you with:\n\n" \
                "- Policy questions (targets, compliance, regulations)\n" \
                "- Emissions data and analysis\n" \
                "- Hotspot identification and recommendations\n" \
                "- Emissions forecasting and trends\n\n" \
                "What would you like to know?"
        
        return {
            'answer': answer,
            'confidence': 1.0,
            'type': 'general'
        }

    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history.
        
        Returns:
            List of conversation messages
        """
        return self.conversation_history

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")


def main():
    """Example usage."""
    assistant = UCIPAssistant()
    
    # Example conversations
    queries = [
        "What are the emissions reduction targets?",
        "Which buildings have the highest emissions?",
        "What will emissions look like next month?",
    ]
    
    for query in queries:
        response = assistant.chat(query)
        logger.info(f"\nQ: {query}")
        logger.info(f"A: {response['answer'][:200]}...")
        logger.info(f"Confidence: {response['confidence']:.2f}")


if __name__ == "__main__":
    main()

