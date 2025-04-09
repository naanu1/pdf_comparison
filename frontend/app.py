import streamlit as st
import requests
import logging
from typing import List, Tuple
from dotenv import load_dotenv
import os

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="PDF Comparison Tool", layout="wide")

def display_differences(differences: List[Tuple[str, str]], view_mode: str = "single") -> None:
    """Display PDF differences with color coding in single or side-by-side view.

    Args:
        differences (List[Tuple[str, str]]): List of (change_type, text) tuples.
        view_mode (str): 'single' or 'side-by-side' display mode.
    """
    if view_mode == "single":
        html_content = "<div style='font-family: Arial; line-height: 1.5;'>"
        for change_type, text in differences:
            if change_type == "added":
                html_content += f"<span style='background-color: #90EE90;'>{text}</span>"
            elif change_type == "removed":
                html_content += f"<span style='background-color: #FFB6C1;'>{text}</span>"
            elif change_type == "modified":
                html_content += f"<span style='background-color: #FFFF99;'>{text}</span>"
            elif change_type == "unchanged":
                html_content += text
            html_content += "<br>"
        html_content += "</div>"
        st.markdown(html_content, unsafe_allow_html=True)
    else:
        left_col, right_col = st.columns(2)
        left_content = "<div style='font-family: Arial; line-height: 1.5;'>"
        right_content = "<div style='font-family: Arial; line-height: 1.5;'>"
        for change_type, text in differences:
            if change_type == "added":
                right_content += f"<span style='background-color: #90EE90;'>{text}</span><br>"
                left_content += "<br>"
            elif change_type == "removed":
                left_content += f"<span style='background-color: #FFB6C1;'>{text}</span><br>"
                right_content += "<br>"
            elif change_type == "modified":
                old, new = text.split("New: ", 1)
                left_content += f"<span style='background-color: #FFFF99;'>{old[5:]}</span><br>"
                right_content += f"<span style='background-color: #FFFF99;'>{new}</span><br>"
            elif change_type == "unchanged":
                left_content += f"{text}<br>"
                right_content += f"{text}<br>"
        left_content += "</div>"
        right_content += "</div>"
        with left_col:
            st.markdown("**Original**")
            st.markdown(left_content, unsafe_allow_html=True)
        with right_col:
            st.markdown("**Modified**")
            st.markdown(right_content, unsafe_allow_html=True)

def main() -> None:
    """Main function to run the Streamlit PDF comparison frontend."""
    st.title("PDF Comparison Tool")
    st.markdown("Upload two PDF files to compare their differences.")

    col1, col2 = st.columns(2)
    with col1:
        pdf1 = st.file_uploader("Upload First PDF", type="pdf", key="pdf1")
    with col2:
        pdf2 = st.file_uploader("Upload Second PDF", type="pdf", key="pdf2")

    view_mode = st.selectbox("View Mode", ["Single View", "Side-by-Side"], index=0)

    if pdf1 and pdf2:
        if st.button("Compare PDFs"):
            with st.spinner("Comparing PDFs..."):
                files = {
                    "pdf1": (pdf1.name, pdf1.read(), "application/pdf"),
                    "pdf2": (pdf2.name, pdf2.read(), "application/pdf"),
                }
                BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
                REQUEST_TIMEOUT = 30

                try:
                    logger.info("Sending request to backend")
                    response = requests.post(
                        f"{BACKEND_URL}/compare-pdfs/",
                        files=files,
                        timeout=REQUEST_TIMEOUT,
                    )
                    response.raise_for_status()
                    result = response.json()

                    st.success("Comparison completed!")
                    summary = result["summary"]
                    st.subheader("Summary of Changes")
                    st.write(f"Additions: {summary['additions']} (Green)")
                    st.write(f"Deletions: {summary['deletions']} (Red)")
                    st.write(f"Modifications: {summary['modifications']} (Yellow)")

                    st.subheader("Detailed Comparison")
                    display_differences(
                        result["differences"],
                        view_mode="single" if view_mode == "Single View" else "side-by-side",
                    )
                except requests.exceptions.ConnectionError:
                    st.error(f"Could not connect to backend at {BACKEND_URL}. Ensure it’s running.")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. Try smaller PDFs or increase timeout.")
                except requests.exceptions.HTTPError as he:
                    st.error(f"Backend error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
                    logger.error(f"Frontend error: {str(e)}")

if __name__ == "__main__":
    main()