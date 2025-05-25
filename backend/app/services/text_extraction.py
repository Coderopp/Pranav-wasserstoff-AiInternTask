import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from fastapi import UploadFile
from typing import List
import logging

from app.models.schemas import (
    ProcessedDocument, DocumentPage, DocumentParagraph, 
    TextPosition, DocumentMetadata
)

logger = logging.getLogger(__name__)

class TextExtractor:
    """Handles text extraction from various file formats"""
    
    @staticmethod
    async def extract_from_file(file: UploadFile) -> ProcessedDocument:
        """Extract text from uploaded file"""
        content = await file.read()
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return await TextExtractor._extract_from_pdf(content, file.filename)
        elif file_extension in ['png', 'jpg', 'jpeg', 'tiff']:
            return await TextExtractor._extract_from_image(content, file.filename)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    @staticmethod
    async def _extract_from_pdf(content: bytes, filename: str) -> ProcessedDocument:
        """Extract text from PDF with position information"""
        pages = []
        full_text = ""
        
        with fitz.open(stream=content, filetype="pdf") as doc:
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                paragraphs = []
                
                # Get text blocks with position information
                blocks = page.get_text("dict")["blocks"]
                
                for block_idx, block in enumerate(blocks):
                    if "lines" in block:
                        paragraph_text = ""
                        for line in block["lines"]:
                            for span in line["spans"]:
                                paragraph_text += span["text"] + " "
                        
                        if paragraph_text.strip():
                            position = TextPosition(
                                page=page_num,
                                paragraph_index=block_idx,
                                rect=list(block["bbox"])
                            )
                            
                            paragraph = DocumentParagraph(
                                text=paragraph_text.strip(),
                                position=position
                            )
                            paragraphs.append(paragraph)
                
                page_obj = DocumentPage(
                    page_number=page_num + 1,
                    paragraphs=paragraphs,
                    full_text=page_text
                )
                pages.append(page_obj)
                full_text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
        
        if not full_text.strip():
            raise ValueError("No text could be extracted from PDF")
        
        return ProcessedDocument(
            id="",  # Will be set by processor
            full_text=full_text.strip(),
            pages=pages,
            metadata=DocumentMetadata(filename=filename, content_type="application/pdf", 
                                    file_size=len(content), upload_date="")
        )
    
    @staticmethod
    async def _extract_from_image(content: bytes, filename: str) -> ProcessedDocument:
        """Extract text from image using OCR"""
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise ValueError(f"Tesseract not properly configured: {str(e)}")
        
        img = Image.open(io.BytesIO(content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        extracted_text = pytesseract.image_to_string(img)
        
        if not extracted_text.strip():
            # Try with different OCR configuration
            extracted_text = pytesseract.image_to_string(
                img, config='--psm 1 --oem 3'
            )
        
        if not extracted_text.strip():
            raise ValueError("No text could be extracted from image")
        
        # Create paragraphs from extracted text
        paragraphs = []
        for i, para_text in enumerate(extracted_text.split('\n\n')):
            if para_text.strip():
                position = TextPosition(page=0, paragraph_index=i, is_ocr=True)
                paragraph = DocumentParagraph(text=para_text.strip(), position=position)
                paragraphs.append(paragraph)
        
        page = DocumentPage(
            page_number=1,
            paragraphs=paragraphs,
            full_text=extracted_text
        )
        
        return ProcessedDocument(
            id="",  # Will be set by processor
            full_text=extracted_text.strip(),
            pages=[page],
            metadata=DocumentMetadata(filename=filename, content_type="image", 
                                    file_size=len(content), upload_date="")
        )