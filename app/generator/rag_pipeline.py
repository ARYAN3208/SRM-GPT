import time
from app.utils.logger import get_logger
from .intent_router import detect_intent
from app.retrieval.retriever import retrieve_documents
from app.generator.reranker import rerank_documents
from .prompt_builder import build_prompt, build_general_prompt
from .llm_generator import generate_answer

logger = get_logger("rag_pipeline")

NOT_FOUND = (
    "I could not find sufficient SRM-specific information to answer this question accurately."
)

RETRIEVAL_POOL_SIZE = 60
FEE_ADMISSION_POOL_SIZE = 80
RERANK_KEEP = 25
FEE_ADMISSION_RERANK_KEEP = 15
DISTANCE_FILTER_THRESHOLD = 1.0
MIN_ACCEPTABLE_DOCS = 10
RELAXED_DISTANCE_THRESHOLD = 1.3
STRICT_DISTANCE_THRESHOLD = 0.7
MIN_GOOD_DOCS = 5


def _general_mode_answer(question, model_name, num_predict, start_time):
    prompt = build_general_prompt(question)
    answer = generate_answer(prompt=prompt, model_name=model_name, num_predict=num_predict)
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
            "answer": NOT_FOUND, "documents": [], "docs_info": [],
            "confidence": 0, "response_time": round(time.time() - start, 2)
        }

    rows = _filter_documents(docs, metas, dists, DISTANCE_FILTER_THRESHOLD)
    if len(rows) < MIN_ACCEPTABLE_DOCS:
        rows = _filter_documents(docs, metas, dists, RELAXED_DISTANCE_THRESHOLD)

    if not rows:
        return {
            "answer": NOT_FOUND, "documents": [], "docs_info": [],
            "confidence": 0, "response_time": round(time.time() - start, 2)
        }

    top_distances = [item[0] for item in rows[:5]]
    avg_distance = sum(top_distances) / len(top_distances)
    confidence = max(0, min(100, round((1 - avg_distance / 2) * 100, 2)))

    if avg_distance <= 0.35:
        retrieval_quality = "excellent"
    elif avg_distance <= 0.7:
        retrieval_quality = "good"
    elif avg_distance <= 1.1:
        retrieval_quality = "weak"
    else:
        retrieval_quality = "poor"

    logger.info("Retrieval quality: %s, confidence: %s", retrieval_quality, confidence)

    raw_docs = []
    docs_info = []
    for dist, doc, meta in rows:
        raw_docs.append(doc)
        docs_info.append({
            "source": meta.get("source", "unknown"),
            "chunk_id": meta.get("chunk_id", "unknown"),
            "distance": round(dist, 4)
        })

    retrieved_docs, reranked_docs_info = rerank_documents(
        query=question, documents=raw_docs, metadatas=docs_info, top_k=rerank_keep
    )

    if avg_distance > STRICT_DISTANCE_THRESHOLD and len(retrieved_docs) < MIN_GOOD_DOCS:
        return {
            "answer": NOT_FOUND, "documents": [], "docs_info": [],
            "confidence": confidence, "response_time": round(time.time() - start, 2)
        }

    prompt = build_prompt(question=question, retrieved_docs=retrieved_docs, metadatas=reranked_docs_info)
    logger.info("Question: %s, docs after rerank: %s, prompt length: %s", question, len(retrieved_docs), len(prompt))

    answer = generate_answer(prompt=prompt, model_name=model_name, num_predict=num_predict)

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

    logger.info("Answer length: %s, confidence: %s", len(answer), confidence_label)
    for item in reranked_docs_info[:5]:
        logger.info("Source: %s", item)

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

    context = ""
    if conversation_history and len(conversation_history) > 0:
        for msg in conversation_history[-4:]:
            role = msg.get("role", "").upper()
            content = msg.get("content", "")[:300]
            context += f"{role}: {content}\n"

    if context:
        enriched_question = f"Context from previous messages:\n{context}\n\nCurrent question: {question}"
    else:
        enriched_question = question

    intent = detect_intent(question)

    if intent == "general":
        return _general_mode_answer(enriched_question, model_name, num_predict, start)

    return _process_retrieval(enriched_question, intent, model_name, num_predict, start)