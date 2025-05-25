from typing import List, Dict, Any
import logging
import json

from groq import Groq

logger = logging.getLogger(__name__)

class LLMService:
    """Handles Large Language Model operations"""
    
    def __init__(self, groq_api_key: str, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=groq_api_key)
        self.model = model
    
    def answer_query(self, query: str, context: str) -> str:
        """Generate answer based on query and context"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Answer the question based on the context provided. Be precise and cite relevant information."
                    },
                    {
                        "role": "user", 
                        "content": f"Question: {query}\n\nContext: {context}"
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def extract_themes(self, documents_text: str) -> List[Dict[str, Any]]:
        """Extract themes from document text"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the provided documents and identify key themes. Return your response as a JSON object with a 'themes' array, where each theme has 'theme_name' and 'document_indices' (array of 0-based indices)."
                    },
                    {
                        "role": "user",
                        "content": f"Identify themes from these documents:\n\n{documents_text}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            themes_data = response.choices[0].message.content
            themes_json = json.loads(themes_data)
            return themes_json.get("themes", [])
        except Exception as e:
            logger.error(f"Error extracting themes: {str(e)}")
            raise