from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pdf_processor import process_pdfs
import aiofiles
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging with a clear format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with metadata
app = FastAPI(
    title="PDF Comparison API",
    description="API to compare text differences between two PDF files",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:8501")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

@app.post("/compare-pdfs/", response_model=dict)
async def compare_pdfs(pdf1: UploadFile = File(...), pdf2: UploadFile = File(...)) -> dict:
    """Compare two PDF files and return their differences and summary.

    Args:
        pdf1 (UploadFile): The first PDF file to compare.
        pdf2 (UploadFile): The second PDF file to compare.

    Returns:
        dict: A dictionary containing 'differences' (list) and 'summary' (dict).

    Raises:
        HTTPException: If file validation fails or processing encounters an error.
    """
    # Validate file extensions
    if not pdf1.filename.endswith(".pdf") or not pdf2.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Define temporary file paths
    pdf1_path = f"temp_{pdf1.filename}"
    pdf2_path = f"temp_{pdf2.filename}"

    try:
        # Check file size before processing
        if pdf1.size > MAX_FILE_SIZE or pdf2.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

        # Write uploaded files asynchronously to temporary locations
        async with aiofiles.open(pdf1_path, "wb") as file1, aiofiles.open(pdf2_path, "wb") as file2:
            await file1.write(await pdf1.read())
            await file2.write(await pdf2.read())

        logger.info(f"Starting processing for PDFs: {pdf1.filename}, {pdf2.filename}")
        differences, summary = process_pdfs(pdf1_path, pdf2_path)
        logger.info("PDF comparison completed successfully")
        return {"differences": differences, "summary": summary}

    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error during PDF comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDFs: {str(e)}")
    finally:
        # Clean up temporary files
        for path in [pdf1_path, pdf2_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    logger.debug(f"Cleaned up temporary file: {path}")
                except OSError as e:
                    logger.warning(f"Failed to remove {path}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)