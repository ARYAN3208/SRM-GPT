import re
from typing import Set

from app.utils.logger import get_logger

logger = get_logger("intent_router")


def contains_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def detect_intent(question: str) -> str:
    q = question.lower().strip()
    q_words = q.split()

    identity_queries = [
        "who are you", "who created you", "what are you", "what is your name",
        "introduce yourself", "tell me about yourself", "your name",
        "what can you do", "how do you work", "who made you",
        "what's your name", "are you ai", "are you chatbot"
    ]
    if any(kw in q for kw in identity_queries):
        logger.info("Intent detected: general (identity query)")
        return "general"

    greeting_short = q in {"hi", "hello", "hey", "heyy", "hii", "hlo", "yo", "sup", "hi there", "hello there"}
    if greeting_short:
        logger.info("Intent detected: general (greeting)")
        return "general"

    gratitude = q in {"thanks", "thank you", "ty", "thankyou", "thanks a lot", "thank you so much"}
    if gratitude:
        logger.info("Intent detected: general (gratitude)")
        return "general"

    person_query_patterns = [
        r"who is\s+(?:dr\.?|prof\.?|professor)?\s*[a-z]",
        r"(?:dr\.?|prof\.?|professor)\s+[a-z]",
        r"hod\s+of\s+[a-z]",
        r"head\s+of\s+department\s+[a-z]",
        r"faculty\s+[a-z]",
        r"[a-z]\.?\s*[a-z]+\s+[a-z]+\s+of\s+[a-z]",
    ]
    if any(re.search(pattern, q) for pattern in person_query_patterns):
        logger.info("Intent detected: srm (person query)")
        return "srm"

    fee_structure_keywords = [
        "fee structure", "complete fee", "full fee", "fee details",
        "fee breakdown", "fee schedule", "tuition fee", "annual fee",
        "total fee", "course fee", "program fee", "hostel fee",
        "mess fee", "fee for b.tech", "fee for m.tech", "fee for mba",
        "fee for bba", "how much fee", "fees for", "fee amount",
        "fee per year", "fee per semester", "cost of", "how much does",
        "what is the fee", "what are the fees", "tell me the fee"
    ]
    fee_related: Set[str] = {"fee", "fees", "cost", "pricing", "price"}
    program_keywords = {
        "b.tech": ["b.tech", "btech"],
        "m.tech": ["m.tech", "mtech"],
        "mba": ["mba"],
        "bba": ["bba"],
        "b.sc": ["b.sc", "bsc"],
        "phd": ["phd"],
        "mca": ["mca"],
        "bca": ["bca"]
    }
    has_fee = any(any(fee_word in word for word in q_words) for fee_word in fee_related)
    has_program = any(any(variant in q for variant in variants) for variants in program_keywords.values())

    if any(keyword in q for keyword in fee_structure_keywords):
        logger.info("Intent detected: fee_structure")
        return "fee_structure"
    if has_fee and has_program:
        logger.info("Intent detected: fee_structure (fee + program)")
        return "fee_structure"

    admission_procedure_keywords = [
        "admission procedure", "admission process", "admission guidelines",
        "how to apply", "admission criteria", "admission requirement",
        "apply for admission", "admission eligibility", "how to get admission",
        "admission in srm", "join srm", "get into srm", "application process",
        "admission for b.tech", "admission for m.tech", "admission for mba",
        "admission for bba", "admission for b.sc", "b.tech admission",
        "m.tech admission", "mba admission", "bba admission",
        "entrance exam for", "srmjeee", "srmjeem", "srmjeel",
        "counselling process", "counselling for", "e-counselling",
        "admission form", "application form", "apply now", "admission open",
        "admission 2025", "admission 2026"
    ]
    if any(keyword in q for keyword in admission_procedure_keywords):
        logger.info("Intent detected: admission_procedure")
        return "admission_procedure"

    academic_policy_keywords = [
        "detain", "detained", "detention", "attendance", "backlog",
        "arrear", "arrears", "failed", "fail", "cgpa", "gpa",
        "condonation", "re-exam", "reexam", "supplementary exam",
        "promotion rule", "regulation"
    ]
    if any(keyword in q for keyword in academic_policy_keywords):
        logger.info("Intent detected: srm (academic policy)")
        return "srm"

    srm_keywords = [
        "srm", "srmist", "ktr",
        "placement", "placements",
        "hostel",
        "scholarship", "scholarships",
        "faculty", "professor", "hod",
        "curriculum", "syllabus",
        "department", "departments",
        "course", "courses",
        "campus",
        "btech", "mtech", "phd",
        "ece", "cse", "aiml", "it",
        "recruiter", "recruiters",
        "semester",
        "academic",
        "laboratory", "lab",
        "workshop", "conference",
        "library",
        "transport",
        "mess",
        "ragging",
        "hostel facility", "hostel facilities",
        "aaruush", "fest", "techno-management", "hackathon",
        "event", "events",
        "anti-ragging"
    ]
    if any(contains_word(q, keyword) for keyword in srm_keywords):
        logger.info("Intent detected: srm (keyword match)")
        return "srm"

    general_indicators = [
        "write code", "programming", "python", "javascript", "react",
        "how to code", "algorithm", "data structure",
        "how are you", "thanks", "thank you",
        "good morning", "good evening",
        "what is ai", "what is machine learning", "tell me a joke",
        "tell me something interesting", "who created", "history of",
        "explain quantum", "explain black hole", "define",
        "how to prepare for interview", "resume tips",
        "how to crack interview", "career in tech"
    ]
    if any(keyword in q for keyword in general_indicators):
        logger.info("Intent detected: general (general indicator)")
        return "general"

    guidance_keywords = [
        "stress", "depression", "mental health", "anxiety",
        "friend problem", "roommate"
    ]
    if any(kw in q for kw in guidance_keywords):
        logger.info("Intent detected: general (guidance)")
        return "general"

    future_keywords = {"2030", "2029", "2028", "future", "predict", "prediction", "forecast"}
    if any(kw in q for kw in future_keywords):
        logger.info("Intent detected: general (future/prediction)")
        return "general"

    generic_help = {"what can i do", "help me", "suggest", "advice", "confused", "worried", "recommend"}
    if any(kw in q for kw in generic_help):
        logger.info("Intent detected: general (help/advice)")
        return "general"

    logger.info("Intent detected: srm (default fallback)")
    return "srm"