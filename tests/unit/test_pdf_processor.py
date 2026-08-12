from pathlib import Path
import fitz
import pytest
from app.workers.pdf_processor import clean_text, extract_text_from_pdf

def test_clean_text():
    # Test 1: None input returns empty string
    assert clean_text(None) == ""

    # Test 2: Strips hyphens at line-breaks, newlines, null bytes, and normalizes spaces
    dirty_input = "docu-\nmentation \n test\0 string  "
    assert clean_text(dirty_input) == "documentation test string"

def test_extract_text_from_nonexistent_pdf():
    # Verify FileNotFoundError is raised when file does not exist
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf("non_existent_file.pdf")

def test_extract_text_from_valid_pdf(tmp_path: Path):
    # 1. Define file path using pytest's temporary folder fixture
    pdf_path = tmp_path / "test_doc.pdf"

    # 2. Generate a 2-page PDF in memory using fitz
    doc = fitz.open()
    
    p1 = doc.new_page()
    p1.insert_text((50, 50), "Atlas RAG Page 1")
    
    p2 = doc.new_page()
    p2.insert_text((50, 50), "Atlas RAG Page 2")
    
    doc.save(str(pdf_path))
    doc.close()

    # 3. Call extract function
    pages = extract_text_from_pdf(pdf_path)

    # 4. Assert extracted data correctness
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert "Atlas RAG Page 1" in pages[0]["text"]
    assert pages[1]["page_number"] == 2
    assert "Atlas RAG Page 2" in pages[1]["text"]
