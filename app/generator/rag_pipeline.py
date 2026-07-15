import time
from app.utils.logger import get_logger
from .intent_router import detect_intent
from app.retrieval.retriever import retrieve_documents
from app.generator.reranker import rerank_documents
from .prompt_builder import build_prompt
from .llm_generator import generate_answer

logger = get_logger("rag_pipeline")

NOT_FOUND = (
    "I could not find sufficient SRM-specific information to answer this question accurately."
)

HIGH_CONFIDENCE = 80
MEDIUM_CONFIDENCE = 60
LOW_CONFIDENCE = 40

# Increased pool sizes for better candidate coverage
RETRIEVAL_POOL_SIZE = 60
FEE_ADMISSION_POOL_SIZE = 80
# Reduced top_k for reranker to keep only the most relevant docs
RERANK_KEEP = 25
FEE_ADMISSION_RERANK_KEEP = 15
# Loosened distance thresholds slightly (all-mpnet-base-v2 has different distribution)
DISTANCE_FILTER_THRESHOLD = 0.40
MIN_ACCEPTABLE_DOCS = 50
RELAXED_DISTANCE_THRESHOLD = 0.50
STRICT_DISTANCE_THRESHOLD = 0.30
MIN_GOOD_DOCS = 25


def _general_mode_answer(question, model_name, num_predict, start_time):
    answer = generate_answer(
        prompt=f"""
You are SRM CampusGPT.

You are a highly intelligent AI assistant.

You can answer:
- General questions
- Technical questions
- Programming questions
- AI questions
- Career questions
- Interview questions
- Small talk

IMPORTANT: If this question asks about specific SRM Institute policies,
rules, numbers, fees, names, dates, or procedures, do NOT guess or invent
an answer. Instead say plainly that you don't have verified SRM-specific
information for this and suggest the person check official SRM sources
or rephrase so the assistant can search SRM's documents directly. Only
answer freely for genuinely general, non-SRM-specific questions.

Question:

{question}

Provide a helpful answer.
""",
        model_name=model_name,
        num_predict=num_predict
    )

    return {
        "answer": answer,
        "documents": [],
        "docs_info": [],
        "confidence": 50,
        "confidence_label": "Ungrounded (General AI - not verified against SRM documents)",
        "response_time": round(time.time() - start_time, 2)
    }


def _filter_documents(docs, metas, dists, threshold):
    rows = []
    for doc, meta, dist in zip(docs, metas, dists):
        if dist > threshold:
            continue
        rows.append((float(dist), doc, meta))
    return rows


def _process_retrieval(question, intent, model_name, num_predict, start):
    if intent in ("fee_structure", "admission_procedure"):
        pool_size = FEE_ADMISSION_POOL_SIZE
        rerank_keep = FEE_ADMISSION_RERANK_KEEP
    else:
        pool_size = RETRIEVAL_POOL_SIZE
        rerank_keep = RERANK_KEEP

    results = retrieve_documents(query=question, top_k=pool_size)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    if not docs:
        return {
            "answer": NOT_FOUND,
            "documents": [],
            "docs_info": [],
            "confidence": 0,
            "response_time": round(time.time() - start, 2)
        }

    rows = _filter_documents(docs, metas, dists, DISTANCE_FILTER_THRESHOLD)

    if len(rows) < MIN_ACCEPTABLE_DOCS:
        rows = _filter_documents(docs, metas, dists, RELAXED_DISTANCE_THRESHOLD)

    if not rows:
        return {
            "answer": NOT_FOUND,
            "documents": [],
            "docs_info": [],
            "confidence": 0,
            "response_time": round(time.time() - start, 2)
        }

    # Compute confidence based on top distances
    top_distances = [item[0] for item in rows[:5]]
    avg_distance = sum(top_distances) / len(top_distances)
    confidence = max(0, min(100, round((1 - avg_distance) * 100, 2)))

    if avg_distance <= 0.20:
        retrieval_quality = "excellent"
    elif avg_distance <= 0.32:
        retrieval_quality = "good"
    elif avg_distance <= 0.42:
        retrieval_quality = "weak"
    else:
        retrieval_quality = "poor"

    print("\n" + "=" * 100)
    print("RETRIEVAL QUALITY")
    print("=" * 100)
    print(retrieval_quality)
    print("\n" + "=" * 100)
    print("CONFIDENCE")
    print("=" * 100)
    print(confidence)

    # Prepare raw docs for reranking - KEEP FULL CONTENT, don't truncate before reranking
    # The reranker needs full text to score relevance accurately
    raw_docs = []
    docs_info = []

    for dist, doc, meta in rows:
        # Keep full document text for reranking; truncation happens only in prompt builder
        raw_docs.append(doc)
        docs_info.append({
            "source": meta.get("source", "unknown"),
            "chunk_id": meta.get("chunk_id", "unknown"),
            "distance": round(dist, 4)
        })

    # Rerank using full document text (not truncated)
    retrieved_docs = rerank_documents(
        query=question,
        documents=raw_docs,
        top_k=rerank_keep
    )

    # Reorder metadata to match reranked docs
    # Build a mapping from original doc text to its metadata
    doc_to_meta = {doc: meta for doc, meta in zip(raw_docs, docs_info)}

    reranked_docs_info = []
    for rdoc in retrieved_docs:
        if rdoc in doc_to_meta:
            reranked_docs_info.append(doc_to_meta[rdoc])
        else:
            reranked_docs_info.append({"source": "unknown", "chunk_id": "unknown", "distance": 0})

    # If retrieval quality is poor AND we have very few reranked docs, return not found
    if avg_distance > STRICT_DISTANCE_THRESHOLD and len(retrieved_docs) < MIN_GOOD_DOCS:
        return {
            "answer": NOT_FOUND,
            "documents": [],
            "docs_info": [],
            "confidence": confidence,
            "response_time": round(time.time() - start, 2)
        }

    # Pass metadatas to prompt builder (was missing before!)
    prompt = build_prompt(question=question, retrieved_docs=retrieved_docs, metadatas=reranked_docs_info)

    print("\n" + "=" * 100)
    print("QUESTION")
    print("=" * 100)
    print(question)
    print("\n" + "=" * 100)
    print("RETRIEVED DOCS (after reranking)")
    print("=" * 100)
    print(len(retrieved_docs))
    print("\n" + "=" * 100)
    print("PROMPT LENGTH")
    print("=" * 100)
    print(len(prompt))

    answer = generate_answer(
        prompt=prompt,
        model_name=model_name,
        num_predict=num_predict
    )

    if not answer or not answer.strip():
        answer = NOT_FOUND
    else:
        answer = answer.strip()

    if confidence >= 80:
        confidence_label = "Excellent"
    elif confidence >= 60:
        confidence_label = "High"
    elif confidence >= 40:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"

    print("\n" + "=" * 100)
    print("ANSWER LENGTH")
    print("=" * 100)
    print(len(answer))
    print("\n" + "=" * 100)
    print("CONFIDENCE LABEL")
    print("=" * 100)
    print(confidence_label)
    print("\n" + "=" * 100)
    print("RAW ANSWER")
    print("=" * 100)
    print(repr(answer))
    print("\n" + "=" * 100)
    print("TOP SOURCES")
    print("=" * 100)

    for item in reranked_docs_info[:5]:
        print(item)

    return {
        "answer": answer,
        "documents": retrieved_docs,
        "docs_info": reranked_docs_info,
        "confidence": confidence,
        "confidence_label": confidence_label,
        "response_time": round(time.time() - start, 2)
    }


def ask_rag(
    question: str,
    model_name: str = "gemini-2.5-flash",
    num_predict: int = 2048,
    conversation_history: list = None
):
    start = time.time()
    question = question.strip()
    
    # Build context from conversation history
    context = ""
    if conversation_history and len(conversation_history) > 0:
        for msg in conversation_history[-4:]:  # Last 4 messages
            role = msg.get("role", "").upper()
            content = msg.get("content", "")[:300]
            context += f"{role}: {content}\n"
    
    # Enrich question with context
    if context:
        enriched_question = f"Context from previous messages:\n{context}\n\nCurrent question: {question}"
    else:
        enriched_question = question
    
    intent = detect_intent(question)

    if intent == "general":
        return _general_mode_answer(enriched_question, model_name, num_predict, start)

    if intent == "fee_structure":
        return _process_retrieval(enriched_question, intent, model_name, num_predict, start)

    if intent == "admission_procedure":
        return _process_retrieval(enriched_question, intent, model_name, num_predict, start)

    return _process_retrieval(enriched_question, intent, model_name, num_predict, start)