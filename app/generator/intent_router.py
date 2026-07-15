import re


def contains_word(text, word):
    return re.search(
        rf"\b{re.escape(word)}\b",
        text
    ) is not None


def detect_intent(question):
    q = question.lower().strip()
    q_words = q.split()
    q_len = len(q)

    # ============ VERY SHORT GREETING / IDENTITY QUERIES ============
    # These are clearly general even if they contain SRM-related words
    identity_queries = [
        "who are you", "who created you", "what are you", "what is your name",
        "introduce yourself", "tell me about yourself", "your name",
        "what can you do", "how do you work", "who made you",
        "what's your name", "are you ai", "are you chatbot"
    ]
    if any(kw in q for kw in identity_queries):
        return "general"

    greeting_short = q in {"hi", "hello", "hey", "heyy", "hii", "hlo", "yo", "sup", "hi there", "hello there"}
    if greeting_short:
        return "general"

    gratitude = q in {"thanks", "thank you", "ty", "thankyou", "thanks a lot", "thank you so much"}
    if gratitude:
        return "general"

    # ============ SRM-SPECIFIC INTENTS (check first) ============

    fee_structure_keywords = [
        "fee structure", "complete fee", "full fee", "fee details",
        "fee breakdown", "fee schedule", "tuition fee", "annual fee",
        "total fee", "course fee", "program fee", "hostel fee",
        "mess fee", "fee for b.tech", "fee for m.tech", "fee for mba",
        "fee for bba", "how much fee", "fees for", "fee amount",
        "fee per year", "fee per semester", "cost of", "how much does",
        "what is the fee", "what are the fees", "tell me the fee"
    ]

    fee_related = {"fee", "fees", "cost", "pricing", "price"}
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

    has_fee = any(
        any(fee_word in word for word in q_words)
        for fee_word in fee_related
    )
    has_program = any(
        any(variant in q for variant in variants)
        for variants in program_keywords.values()
    )

    if any(keyword in q for keyword in fee_structure_keywords):
        return "fee_structure"

    if has_fee and has_program:
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
        return "admission_procedure"

    # ============ ACADEMIC POLICIES (SRM-specific) ============

    academic_policy_keywords = [
        "detain", "detained", "detention", "attendance", "backlog",
        "arrear", "arrears", "failed", "fail", "cgpa", "gpa",
        "condonation", "re-exam", "reexam", "supplementary exam",
        "promotion rule", "regulation"
    ]

    if any(keyword in q for keyword in academic_policy_keywords):
        return "srm"

    # ============ BROAD SRM KEYWORDS ============

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
        return "srm"

    # ============ GENERAL INTENT (truly general queries) ============

    general_indicators = [
        # Programming & technical
        "write code", "programming", "python", "javascript", "react",
        "how to code", "algorithm", "data structure",
        # Small talk
        "how are you", "thanks", "thank you",
        "good morning", "good evening",
        # General knowledge (non-SRM)
        "what is ai", "what is machine learning", "tell me a joke",
        "tell me something interesting", "who created", "history of",
        "explain quantum", "explain black hole", "define",
        # Career advice (general, not SRM-specific)
        "how to prepare for interview", "resume tips",
        "how to crack interview", "career in tech"
    ]

    if any(keyword in q for keyword in general_indicators):
        return "general"

    # Emotional/guidance keywords - route to general
    guidance_keywords = [
        "stress", "depression", "mental health", "anxiety",
        "friend problem", "roommate"
    ]

    if any(kw in q for kw in guidance_keywords):
        return "general"

    # Future/prediction keywords - route to general
    future_keywords = ["2030", "2029", "2028", "future", "predict",
                       "prediction", "forecast"]
    if any(kw in q for kw in future_keywords):
        return "general"

    # Generic "help me", "advice", "suggest"
    generic_help = ["what can i do", "help me", "suggest", "advice",
                    "confused", "worried", "recommend"]
    if any(kw in q for kw in generic_help):
        return "general"

    # Default: route to SRM retrieval (better to attempt search than give ungrounded answer)
    return "srm"