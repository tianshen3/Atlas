import re
from pathlib import Path
from typing import Any, Dict, List
import pymupdf as fitz
import structlog
import tiktoken

logger = structlog.get_logger(__name__)

# cleans the text to be stored in the vector db after processing
def clean_text(text: str) -> str:
    if text is None:
        return ""
    text = text.replace("-\n", "")
    text = text.replace("\n", " ") 
    text = text.replace("\0", " ")
    text = " ".join(text.split())
    return text


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentence boundaries using punctuation lookaheads."""
    sentence_endings = re.compile(r'(?<=[.?!])\s+(?=[A-Z0-9"\'])')
    raw_sentences = sentence_endings.split(text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences or [text]


# this function will extract the text from the pdf using pymupdf instance fitz
def extract_text_from_pdf(file_path: Path | str) -> List[Dict[str, Any]]:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found at {path}")

    doc = fitz.open(str(path))
    extracted_pages: List[Dict[str, Any]] = []

    for page_num, page in enumerate(doc, start=1):
        raw_text = page.get_text("text")
        cleaned_text = clean_text(raw_text)
        extracted_pages.append({
            "page_number": page_num,
            "text": cleaned_text,
        })

    doc.close()
    logger.info("pdf_text_extracted", file_path=str(path), page_count=len(extracted_pages))
    return extracted_pages


def chunk_document_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = 510,
    chunk_overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Lightweight, sentence-aware token chunker using tiktoken (cl100k_base).
    Avoids heavy ML/AST dependencies like LlamaIndex, NLTK, or NetworkX to stay well under 512MB RAM.
    """
    encoder = tiktoken.get_encoding("cl100k_base")
    chunks = []
    global_chunk_index = 0

    for page in pages:
        page_number = page.get("page_number", 1)
        text = (page.get("text") or "").strip()
        if not text:
            logger.warning("Skipping empty page", page_number=page_number)
            continue

        sentences = split_into_sentences(text)
        current_chunk_sentences: List[str] = []
        current_token_count = 0

        for sentence in sentences:
            sentence_tokens = len(encoder.encode(sentence))

            # Handle edge case where a single sentence exceeds the chunk window
            if sentence_tokens > chunk_size:
                if current_chunk_sentences:
                    chunk_str = " ".join(current_chunk_sentences)
                    chunks.append({
                        "chunk_index": global_chunk_index,
                        "page_number": page_number,
                        "text": chunk_str,
                        "token_count": current_token_count,
                    })
                    global_chunk_index += 1
                    current_chunk_sentences = []
                    current_token_count = 0

                encoded = encoder.encode(sentence)
                start = 0
                step = max(1, chunk_size - chunk_overlap)
                while start < len(encoded):
                    end = min(start + chunk_size, len(encoded))
                    chunk_text = encoder.decode(encoded[start:end])
                    chunks.append({
                        "chunk_index": global_chunk_index,
                        "page_number": page_number,
                        "text": chunk_text,
                        "token_count": end - start,
                    })
                    global_chunk_index += 1
                    start += step
                continue

            # If appending sentence exceeds chunk_size, emit current chunk
            if current_token_count + sentence_tokens > chunk_size and current_chunk_sentences:
                chunk_str = " ".join(current_chunk_sentences)
                chunks.append({
                    "chunk_index": global_chunk_index,
                    "page_number": page_number,
                    "text": chunk_str,
                    "token_count": current_token_count,
                })
                global_chunk_index += 1

                # Overlap: preserve trailing sentences that fit within chunk_overlap
                overlap_sentences: List[str] = []
                overlap_tokens = 0
                for prev_s in reversed(current_chunk_sentences):
                    prev_tokens = len(encoder.encode(prev_s))
                    if overlap_tokens + prev_tokens <= chunk_overlap:
                        overlap_sentences.insert(0, prev_s)
                        overlap_tokens += prev_tokens
                    else:
                        break
                current_chunk_sentences = overlap_sentences
                current_token_count = overlap_tokens

            current_chunk_sentences.append(sentence)
            current_token_count += sentence_tokens

        # Emit remaining sentences on this page
        if current_chunk_sentences:
            chunk_str = " ".join(current_chunk_sentences)
            chunks.append({
                "chunk_index": global_chunk_index,
                "page_number": page_number,
                "text": chunk_str,
                "token_count": current_token_count,
            })
            global_chunk_index += 1

    logger.info("pdf_text_chunked", total_chunks=len(chunks))
    return chunks


