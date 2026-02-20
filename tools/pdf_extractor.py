"""PDF extraction tool for Seeker agent."""
from typing import Dict, Any
from .base import BaseTool
import PyPDF2


class PDFExtractorTool(BaseTool):
    """Tool for extracting text from PDF files."""
    
    name = "pdf_extractor"
    description = "Extract text content from a PDF file"
    parameters = {
        "pdf_path": {
            "type": "string",
            "description": "Path to the PDF file to extract text from"
        }
    }
    
    def execute(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text from the PDF
        """
        try:
            # Open the PDF file
            with open(pdf_path, 'rb') as file:
                # Create PDF reader object
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"