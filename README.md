# PDF Comparison Tool

A web application to compare two PDF files, highlighting differences with color coding (green for additions, red for deletions, yellow for modifications). Built with FastAPI (backend) and Streamlit (frontend).

## Features

- Upload two PDFs and compare their text content.
- Supports text-based and scanned PDFs.
- Single or side-by-side view modes.
- Summary of changes (additions, deletions, modifications).

## Project Structure

pdf_comparison_tool/
├── backend/ # FastAPI backend
│ ├── main.py
│ └── pdf_processor.py
├── frontend/ # Streamlit frontend
│ └── app.py
├── .env # Environment variables
└── requirements.txt # Dependencies

## Prerequisites

- Python 3.9+
- Tesseract OCR installed (for scanned PDFs)

## Quick Start

1.Clone the repo:

```
git clone https://github.com/naanu1/pdf_comparison.git
cd pdf_comparison_tool

2.create virtual environment
python -m venv venv
source venv/bin/activate

3.Install dependencies:
pip install -r requirements.txt

4.Run the backend:
cd backend
uvicorn main:app --reload

5.Run the frontend (new terminal):
cd frontend
streamlit run app.py
Open http://localhost:8501 in your browser.
```
