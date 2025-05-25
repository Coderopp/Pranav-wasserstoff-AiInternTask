import re
from typing import List
import nltk
from nltk.tokenize import sent_tokenize

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class TextSegmenter:
    """Handles text segmentation into paragraphs and sentences"""
    
    @staticmethod
    def segment_text(text: str) -> List[str]:
        """Segment text into meaningful chunks"""
        if not text:
            return []
        
        # Split into paragraphs first
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        if len(paragraphs) > 1:
            return paragraphs
        
        # If single paragraph, split into sentences
        if paragraphs:
            return sent_tokenize(paragraphs[0])
        
        return []