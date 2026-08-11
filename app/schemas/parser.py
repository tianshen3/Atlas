from typing import List
from pydantic import BaseModel, Field


class ParsedPage(BaseModel):
    """Schema representing text content and metadata extracted from a single PDF page."""

    page_number: int = Field(..., description="1-indexed page number of the PDF", gt=0)
    text: str = Field(..., description="Cleaned text content extracted from the page")
    char_count: int = Field(..., description="Total character count of the page text", ge=0)


class ParsedDocument(BaseModel):
    """Schema representing aggregated text content and metadata for an entire PDF document."""

    filename: str = Field(..., description="Original filename of the parsed PDF")
    total_pages: int = Field(..., description="Total page count in the document", ge=0)
    pages: List[ParsedPage] = Field(default_factory=list, description="List of parsed pages")
    total_chars: int = Field(..., description="Total aggregate character count across all pages", ge=0)
