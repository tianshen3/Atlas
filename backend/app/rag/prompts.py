from typing import Any
from app.schemas.retrieval import SearchResultChunk

SYSTEM_PROMPT_TEMPLATE = """You are ATLAS, an authoritative enterprise AI assistant.
Your purpose is to answer the user's question accurately using ONLY the verified context snippets provided inside the <context> XML tags below.

[RULES]
1. Answer factual questions using ONLY information explicitly stated inside the <context> block.
2. For conversational greetings (such as "hi", "hello", "who are you"), politely greet the user as ATLAS and briefly state what topics or documents are available in the provided context.
3. If a specific factual question cannot be deduced from the provided context, state:
   "I cannot find sufficient information in the provided enterprise documents to answer this question."
4. Do NOT invent or speculate beyond what the documents contain.
5. Every factual claim derived from context must be followed by an inline citation referencing the source index number, formatted as: [Source X] (e.g., [Source 1], [Source 2]).
================================================================================
[RETRIEVED CONTEXT SNIPPETS]
================================================================================
<context>
{context_block}
</context>"""

# a helper function for building grounded messages
def format_context_block(chunks: list[SearchResultChunk]) -> str:
    formatted_snippets = []

    for idx, chunk in enumerate(chunks, start=1):
        meta = chunk.metadata or {}
        file_name = meta.get("file_name", "Unknown")
        page_number = meta.get("page_number", "N/A")

        snippet = (
            f"[Source {idx}]\n"
            f"Document ID: {chunk.document_id}\n"
            f"File Name: {file_name}\n"
            f"Page Number: {page_number}\n"
            f"Content:\n{chunk.content}"
        )
        formatted_snippets.append(snippet)

    return "\n\n".join(formatted_snippets)



def build_grounded_messages(query: str, chunks: list[SearchResultChunk]) -> list[dict[str, str]] :
    context_block = format_context_block(chunks)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context_block = context_block)

    return [
        {"role": "system" , "content": system_prompt},
        {"role": "user", "content": query}
    ]