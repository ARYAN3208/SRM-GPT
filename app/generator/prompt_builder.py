import logging
from typing import List, Dict, Tuple

logger = logging.getLogger("prompt_builder")

# Increased limits to give the LLM more context to work with
MAX_DOCS = 15
MAX_CHARS_PER_DOC = 4000
MAX_CONTEXT_CHARS = 15000
MAX_PROMPT_TOKENS = 12000


def sanitize_context(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = "\n".join(line.rstrip() for line in text.split("\n") if line.strip())
    text = "".join(c for c in text if ord(c) >= 32 or c in '\n\t')
    return text.strip()


def build_context_from_retrieval(
    retrieved_docs: List[str],
    metadatas: List[Dict] = None,
    max_docs: int = MAX_DOCS,
    max_chars_per_doc: int = MAX_CHARS_PER_DOC
) -> Tuple[str, List[Dict]]:
    if not retrieved_docs:
        logger.warning("No retrieved documents provided")
        return "", []

    context_parts = []
    sources_used = []
    total_chars = 0

    for idx, doc in enumerate(retrieved_docs[:max_docs], start=1):
        if not isinstance(doc, str) or not doc.strip():
            logger.debug(f"Skipping invalid document {idx}")
            continue

        doc_clean = sanitize_context(doc)
        if len(doc_clean) > max_chars_per_doc:
            logger.debug(f"Document {idx} truncated from {len(doc_clean)} to {max_chars_per_doc} chars")
            doc_clean = doc_clean[:max_chars_per_doc] + "..."

        meta = {}
        if metadatas and idx - 1 < len(metadatas):
            meta_raw = metadatas[idx - 1]
            if isinstance(meta_raw, dict):
                meta = {
                    "chunk_id": str(meta_raw.get("chunk_id", "unknown"))[:30],
                    "source": str(meta_raw.get("source", "unknown"))[:50],
                    "distance": meta_raw.get("distance", 0)
                }
            else:
                meta = {"source": "unknown", "chunk_id": "unknown"}

        source_label = meta.get("source", f"Document {idx}")
        context_entry = f"[SOURCE: {source_label}]\n{doc_clean}\n"

        if total_chars + len(context_entry) > MAX_CONTEXT_CHARS:
            logger.info(f"Context limit reached at document {idx}, total: {total_chars} chars")
            break

        context_parts.append(context_entry)
        sources_used.append(meta)
        total_chars += len(context_entry)

    context = "\n".join(context_parts)
    logger.info(f"Built context: {len(context)} chars from {len(context_parts)} documents")
    return context, sources_used


def build_prompt(
    question: str,
    retrieved_docs: List[str],
    metadatas: List[Dict] = None
) -> str:
    if not question or len(question.strip()) < 2:
        logger.error("Invalid question provided")
        question = "Unable to process question"

    if not retrieved_docs:
        logger.warning("No documents provided for prompt building")

    context, sources_used = build_context_from_retrieval(
        retrieved_docs, metadatas,
        max_docs=MAX_DOCS,
        max_chars_per_doc=MAX_CHARS_PER_DOC
    )

    question_clean = sanitize_context(question)
    logger.info(f"Building prompt for question: {question_clean[:50]}...")
    logger.info(f"Context: {len(context)} chars, Sources: {len(sources_used)}")

    final_prompt = f"""You are SRM CampusGPT, an AI assistant for SRM Institute of Science and Technology.

Answer the following question using ONLY the SRM information provided below.

====================================================
SRM INFORMATION (from Knowledge Base)
====================================================

{context}

====================================================
USER QUESTION
====================================================

{question_clean}

====================================================
INSTRUCTIONS (IMPORTANT - Follow these strictly)
====================================================

CRITICAL RULES:
1. Use ONLY the supplied SRM information above. NEVER invent facts, fees, names, numbers, or statistics.
2. Present information AS-IS - be direct and factual. Do NOT add disclaimers like "fees subject to change" or "please verify".
3. Focus only on information relevant to the question. Ignore unrelated content in the context.
4. If the information is found, present it completely and confidently. Do NOT say "based on the provided information" or "according to the documents".
5. Do NOT mention: context, documents, database, retrieval, knowledge base, or any technical RAG terminology.
6. Use headings, bullet points, and tables where appropriate. Keep answers professional and well-structured.
7. If the context contains NO useful information to answer the question, simply state: "I could not find sufficient SRM-specific information to answer this question accurately."

For admission questions: Include eligibility, exam, process, counselling, fees.
For fee questions: Give exact amounts with programme names. Separate components clearly.
For hostel questions: Cover room types, facilities, fees, mess details.
For placement questions: Provide statistics, packages, recruiters.
For faculty questions: Names, designations, departments.
For lab questions: Names, facilities, equipment.

IMPORTANT: Extract and present the relevant information in a well-structured format. Do not omit key details like exact fees, contact emails, or specific program names. If the context has the exact answer, present it directly."""

    estimated_tokens = len(final_prompt) // 4
    logger.info(f"Final prompt length: {len(final_prompt)} chars (~{estimated_tokens} tokens)")

    # Check if prompt is too long and log warning
    if estimated_tokens > MAX_PROMPT_TOKENS:
        logger.warning(f"Prompt exceeds token estimate: {estimated_tokens} tokens (limit: {MAX_PROMPT_TOKENS})")

    return final_prompt