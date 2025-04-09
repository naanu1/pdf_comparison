import pdfplumber
from difflib import Differ
import pytesseract
from PIL import Image
import io
import logging
import os
from typing import Tuple, List, Dict

# Configure logging
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file: str) -> str:
    """Extract text from a PDF file, falling back to OCR if necessary.

    Args:
        pdf_file (str): Path to the PDF file.

    Returns:
        str: Extracted text from the PDF.

    Raises:
        ValueError: If the file is invalid, empty, or no text is extracted.
    """
    # Validate file existence and basic integrity
    if not os.path.exists(pdf_file) or os.path.getsize(pdf_file) == 0:
        raise ValueError(f"Invalid PDF file: {pdf_file} does not exist or is empty")

    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Attempt direct text extraction
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    logger.debug(f"Page {page_num}: Extracted {len(page_text)} characters")
                else:
                    # Fallback to OCR for scanned or image-based pages
                    logger.info(f"Page {page_num}: No text found, attempting OCR")
                    if page.images:
                        for img_idx, img in enumerate(page.images, 1):
                            try:
                                img_data = img["stream"].get_data()
                                img_pil = Image.open(io.BytesIO(img_data))
                                ocr_text = pytesseract.image_to_string(img_pil)
                                text += ocr_text + "\n"
                                logger.debug(f"Page {page_num}, Image {img_idx}: OCR extracted {len(ocr_text)} chars")
                            except Exception as img_e:
                                logger.warning(f"OCR failed for image {img_idx} on page {page_num}: {str(img_e)}")

        # Check if any text was extracted
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF (empty or unsupported format)")

        logger.info(f"Total text extracted from {pdf_file}: {len(text)} characters")
        return text

    except pdfplumber.pdfminer.PDFSyntaxError:
        raise ValueError(f"Invalid PDF structure in {pdf_file}: Missing /Root object or corrupted")
    except Exception as e:
        logger.error(f"Text extraction failed for {pdf_file}: {str(e)}")
        raise ValueError(f"Failed to extract text: {str(e)}")

def compare_texts(text1: str, text2: str) -> Tuple[List[Tuple[str, str]], Dict[str, int]]:
    """Compare two texts line-by-line and categorize differences.

    Args:
        text1 (str): Text from the first PDF.
        text2 (str): Text from the second PDF.

    Returns:
        Tuple[List[Tuple[str, str]], Dict[str, int]]: Differences list and summary dictionary.
    """
    try:
        # Initialize Differ for line-by-line comparison
        differ = Differ()
        diff = list(differ.compare(text1.splitlines(keepends=True), text2.splitlines(keepends=True)))

        differences: List[Tuple[str, str]] = []
        summary: Dict[str, int] = {"additions": 0, "deletions": 0, "modifications": 0}
        index = 0

        # Process the diff output
        while index < len(diff):
            line = diff[index]
            if line.startswith("+ "):
                differences.append(("added", line[2:]))
                summary["additions"] += 1
                index += 1
            elif line.startswith("- "):
                if index + 1 < len(diff) and diff[index + 1].startswith("+ "):
                    differences.append(("modified", f"Old: {line[2:]}New: {diff[index + 1][2:]}"))
                    summary["modifications"] += 1
                    index += 2
                else:
                    differences.append(("removed", line[2:]))
                    summary["deletions"] += 1
                    index += 1
            elif line.startswith("  "):
                differences.append(("unchanged", line[2:]))
                index += 1
            else:
                index += 1  # Skip '?' lines (character-level diff markers)

        logger.info(f"Text comparison completed: {summary}")
        return differences, summary

    except Exception as e:
        logger.error(f"Failed to compare texts: {str(e)}")
        raise ValueError(f"Text comparison failed: {str(e)}")

def process_pdfs(pdf1_path: str, pdf2_path: str) -> Tuple[List[Tuple[str, str]], Dict[str, int]]:
    """Process two PDF files and return their comparison results.

    Args:
        pdf1_path (str): Path to the first PDF file.
        pdf2_path (str): Path to the second PDF file.

    Returns:
        Tuple[List[Tuple[str, str]], Dict[str, int]]: Differences and summary of changes.

    Raises:
        ValueError: If file size exceeds limit or processing fails.
    """
    try:
        # Define constants
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

        # Validate file sizes
        if os.path.getsize(pdf1_path) > MAX_FILE_SIZE or os.path.getsize(pdf2_path) > MAX_FILE_SIZE:
            raise ValueError("File size exceeds 10MB limit")

        # Extract text from both PDFs
        text1 = extract_text_from_pdf(pdf1_path)
        text2 = extract_text_from_pdf(pdf2_path)

        # Compare the extracted texts
        differences, summary = compare_texts(text1, text2)
        return differences, summary

    except ValueError as ve:
        logger.error(f"Processing error: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in PDF processing: {str(e)}")
        raise ValueError(f"PDF processing failed: {str(e)}")