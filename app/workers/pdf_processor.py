from pathlib import Path
from typing import List, Dict, Any
import fitz
import structlog

logger = structlog.get_logger(__name__)

# cleans the text to be stored in the vector db after processing
def clean_text(text: str) -> str:
    
    # checks if the text is empty or not
    if text is None: return ""

    # if text is not empty then remove the hypenated lines
    text = text.replace("-\n", "")

    # now replace the newlines with single spaces
    text = text.replace("\n", " ") 

    # remove remove the null byte
    text = text.replace("\0", " ")

    # normalize the spaces
    text = " ".join(text.split())

    return text


def extract_text_from_pdf(file_path: Path | str) -> List[Dict[str, Any]]:

    # convert the file path to path object
    path = Path(file_path)

    # check if the file exists
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found at {path}")

    # open the pdf document as doc
    doc = fitz.open(str(path))
    extracted_pages: List[Dict[str, Any]] = []

    # iterate over the each pages and extract the text
    for page_num, page in enumerate(doc, start = 1):
        raw_text = page.get_text("text")
        cleaned_text = clean_text(raw_text)
        extracted_pages.append({
            "page_number": page_num,
            "text": cleaned_text,
        })

    # close the the document to free up resources
    doc.close()

    # logging the success
    logger.info("pdf_text_extracted", file_path = str(path), page_count = len(extracted_pages))

    return extracted_pages






