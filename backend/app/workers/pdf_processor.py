from pathlib import Path
from typing import List, Dict, Any
import fitz
import structlog

import tiktoken
from llama_index.core.node_parser import SentenceSplitter

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

# this function will extract the text from the pdf using pymupdf instance fitz
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

# this will will chunking text using llama-index 
def chunk_document_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = 510,
    chunk_overlap: int = 50,
) -> List[Dict[str, Any]]:

    # intilazing the tiktoken tokenizer
    encoder = tiktoken.get_encoding("cl100k_base")

    # initializing the sentence splitter
    splitter = SentenceSplitter(chunk_size = chunk_size, chunk_overlap = chunk_overlap, )

    chunks = []
    global_chunk_index = 0

    for page in pages:
        page_number = page["page_number"]
        text = page["text"]

        # checks if the page text is empty or not
        if not text.strip():
            logger.warning("Skipping empty page", page_number = page_number)
            continue
        
        # creating chunks of the text of a given page number
        page_chunks = splitter.split_text(text)

        for chunk_text in page_chunks:
            
            # this represent the no. of tokens needed to represent those chunks
            token_count = len(encoder.encode(chunk_text))

            chunks.append({
                "chunk_index": global_chunk_index,
                "page_number": page_number,
                "text": chunk_text,
                "token_count": token_count,
            })
            global_chunk_index += 1
    
    # log the total result
    logger.info("pdf_text_chunked", total_chunks = len(chunks))

    return chunks
    






