from typing import List, Dict, Tuple

from app.utils.logger import get_logger

logger = get_logger("prompt_builder")

MAX_DOCS = 15
MAX_CHARS_PER_DOC = 4000
MAX_CONTEXT_CHARS = 15000
MAX_PROMPT_TOKENS = 12000

SRM_FULL_FORM = 'Sri Ramaswamy Memorial'


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
        max_docs=MAX_DOCS, max_chars_per_doc=MAX_CHARS_PER_DOC
    )
    question_clean = sanitize_context(question)
    logger.info(f"Building prompt for question: {question_clean[:50]}...")
    logger.info(f"Context: {len(context)} chars, Sources: {len(sources_used)}")

    not_found_msg = 'I could not find sufficient SRM-specific information to answer this question accurately.'

    final_prompt = (
        'You are SRM CampusGPT, an AI assistant for SRM Institute of Science and Technology.\n\n'
        'Answer the user\'s question using ONLY the SRM information below.\n\n'
        'CONTEXT:\n'
        f'{context}\n\n'
        'QUESTION: ' + question_clean + '\n\n'
        'INSTRUCTIONS:\n'
        '- Provide a complete and thorough answer using all relevant information from the context.\n'
        '- Include eligibility criteria, specific numbers, fees, percentages, dates, and requirements.\n'
        '- Organize the answer with clear sections using **bold headings** for each major point.\n'
        '- Use bullet points to list items clearly.\n'
        '- If the question is about a specific department, include only information about that department.\n'
        '- If the context has nothing relevant, say: "' + not_found_msg + '"\n'
        '- Present the information directly. Do not say \'based on the context\' or \'according to the documents\'.'
    )

    estimated_tokens = len(final_prompt) // 4
    logger.info(f"Final prompt length: {len(final_prompt)} chars (~{estimated_tokens} tokens)")
    if estimated_tokens > MAX_PROMPT_TOKENS:
        logger.warning(f"Prompt exceeds token estimate: {estimated_tokens} tokens (limit: {MAX_PROMPT_TOKENS})")
    return final_prompt


def build_general_prompt(question: str) -> str:
    question_clean = sanitize_context(question)
    logger.info(f"Building general prompt for question: {question_clean[:50]}...")
    return (
        'You are SRM CampusGPT.\n\n'
        'You are a highly intelligent AI assistant.\n\n'
        'You can answer:\n'
        '- General questions\n'
        '- Technical questions\n'
        '- Programming questions\n'
        '- AI questions\n'
        '- Career questions\n'
        '- Interview questions\n'
        '- Small talk\n\n'
        'IMPORTANT: If this question asks about specific SRM Institute policies,\n'
        'rules, numbers, fees, names, dates, or procedures, do NOT guess or invent\n'
        'an answer. Instead say plainly that you don\'t have verified SRM-specific\n'
        'information for this and suggest the person check official SRM sources\n'
        'or rephrase so the assistant can search SRM\'s documents directly. Only\n'
        'answer freely for genuinely general, non-SRM-specific questions.\n\n'
        'Question:\n\n'
        f'{question_clean}\n\n'
        'Provide a helpful answer.'
    )