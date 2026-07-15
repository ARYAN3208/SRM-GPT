import os
import logging
import re
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger("llm_generator")

groq_client = None
_gemini_configured = False
_gemini_client_cache = None

# Configuration
MAX_PROMPT_LENGTH = 32000
MAX_RESPONSE_TOKENS = 4096
TEMPERATURE_DEFAULT = 0.7
TEMPERATURE_GROQ = 0.3

def sanitize_prompt(prompt: str) -> str:
    """Remove prompt injection patterns."""
    dangerous_patterns = [
        r"ignore.*instruction",
        r"forget.*context",
        r"system.*override",
        r"developer.*mode",
        r"bypass.*safety",
        r"act as.*jailbreak"
    ]
    sanitized = prompt
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    
    # Truncate to max length - keep the END (context) not the beginning (instructions)
    if len(sanitized) > MAX_PROMPT_LENGTH:
        logger.warning(f"Prompt truncated from {len(prompt)} to {MAX_PROMPT_LENGTH} chars")
        sanitized = sanitized[-MAX_PROMPT_LENGTH:]
    
    return sanitized.strip()

def _get_gemini_client():
    global _gemini_configured, _gemini_client_cache

    try:
        import google.generativeai as genai
        import google.api_core.exceptions as google_exceptions
    except ImportError as exc:
        logger.error("Gemini not installed: %s", exc)
        raise RuntimeError(
            "Gemini support requires google-generativeai. "
            "Install it or choose another model."
        ) from exc

    if not _gemini_configured:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not set")
            raise RuntimeError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        _gemini_configured = True
        logger.info("Gemini client configured")

    return genai

def _get_groq_client():
    global groq_client

    if groq_client is not None:
        return groq_client

    groq_key = os.getenv("GROQ_API_KEY")

    if not groq_key:
        logger.error("GROQ_API_KEY not set")
        raise RuntimeError("Groq API Key missing. Set GROQ_API_KEY environment variable.")

    try:
        from groq import Groq
    except ImportError as exc:
        logger.error("Groq not installed: %s", exc)
        raise RuntimeError(
            "Groq support requires the groq package. "
            "Install it or choose another model."
        ) from exc

    groq_client = Groq(api_key=groq_key)
    logger.info("Groq client initialized")
    return groq_client

def _get_ollama_chat():
    try:
        from ollama import chat
    except ImportError as exc:
        logger.error("Ollama not installed: %s", exc)
        raise RuntimeError(
            "Ollama support requires the ollama package. "
            "Install it or choose another model."
        ) from exc

    return chat

def _generate_gemini(
    prompt: str,
    model_name: str
) -> str:
    """Generate response using Gemini."""
    try:
        logger.info(f"Calling Gemini model: {model_name}")
        
        genai = _get_gemini_client()
        model = genai.GenerativeModel(model_name)

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": TEMPERATURE_DEFAULT,
                "max_output_tokens": MAX_RESPONSE_TOKENS,
                "top_p": 0.95
            }
        )

        if not response or not response.text:
            logger.warning("Empty response from Gemini")
            return "No response generated."

        logger.info(f"Gemini response length: {len(response.text)} chars")
        return response.text

    except Exception as exc:
        logger.error(f"Gemini generation failed: {exc}", exc_info=True)
        raise

def _generate_groq(
    prompt: str,
    model_name: str,
    num_predict: int,
    is_general_mode: bool = False
) -> str:
    """Generate response using Groq."""
    try:
        logger.info(f"Calling Groq model: {model_name}")
        
        client = _get_groq_client()

        model_map = {
            "llama-3.3-70b": "llama-3.3-70b-versatile",
            "llama-3.1-70b": "llama-3.1-70b-versatile"
        }

        groq_model = model_map.get(model_name)

        if groq_model is None:
            logger.error(f"Unknown Groq model: {model_name}")
            raise ValueError(f"Unknown Groq model: {model_name}")

        system_content = (
            "You are a helpful general AI assistant."
            if is_general_mode
            else "You are a helpful SRM University knowledge assistant. Answer using only the provided context."
        )

        response = client.chat.completions.create(
            model=groq_model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE_GROQ,
            max_tokens=min(num_predict, 4096)
        )

        if not response or not response.choices:
            logger.warning("Empty response from Groq")
            return "No response generated."

        answer = response.choices[0].message.content
        logger.info(f"Groq response length: {len(answer)} chars")
        return answer

    except Exception as exc:
        logger.error(f"Groq generation failed: {exc}", exc_info=True)
        raise

def _generate_ollama(
    prompt: str,
    model_name: str
) -> str:
    """Generate response using Ollama (local)."""
    try:
        logger.info(f"Calling Ollama model: {model_name}")
        
        local_model = model_name.replace("ollama:", "")

        chat = _get_ollama_chat()

        response = chat(
            model=local_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful SRM University knowledge assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        if not response or "message" not in response:
            logger.warning("Empty response from Ollama")
            return "No response generated."

        answer = response["message"]["content"]
        logger.info(f"Ollama response length: {len(answer)} chars")
        return answer

    except Exception as exc:
        logger.error(f"Ollama generation failed: {exc}", exc_info=True)
        raise

def generate_answer(
    prompt: str,
    model_name: str = "gemini-2.5-flash",
    num_predict: int = MAX_RESPONSE_TOKENS
) -> str:
    """
    Generate answer using specified model with fallback support.
    
    Args:
        prompt: The prompt to send to the LLM
        model_name: Model to use (gemini-*, llama-3.3-70b, ollama:*)
        num_predict: Max tokens to generate
    
    Returns:
        Generated answer string
    """
    if not prompt or len(prompt.strip()) < 2:
        logger.error("Invalid prompt provided")
        return "Error: Invalid prompt."

    # Sanitize prompt
    safe_prompt = sanitize_prompt(prompt)

    try:
        logger.info(f"Generating answer with model: {model_name}, prompt length: {len(safe_prompt)}")

        if model_name.startswith("gemini"):
            return _generate_gemini(safe_prompt, model_name)

        elif model_name == "llama-3.3-70b":
            return _generate_groq(safe_prompt, model_name, num_predict)

        elif model_name.startswith("ollama:"):
            return _generate_ollama(safe_prompt, model_name)

        else:
            error_msg = f"Unsupported model: {model_name}"
            logger.error(error_msg)
            return error_msg

    except Exception as e:
        error_text = str(e).lower()
        logger.warning(f"Primary model failed: {error_text}")

        # Fallback: Try Groq if available
        if "quota" in error_text or "429" in error_text:
            logger.info("Quota/rate limit hit, trying Groq fallback...")
            if os.getenv("GROQ_API_KEY"):
                try:
                    return _generate_groq(safe_prompt, "llama-3.3-70b", num_predict)
                except Exception as groq_exc:
                    logger.error(f"Groq fallback failed: {groq_exc}")

            # Fallback: Try Ollama
            logger.info("Trying Ollama fallback...")
            try:
                return _generate_ollama(safe_prompt, "ollama:llama3:8b")
            except Exception as ollama_exc:
                logger.error(f"Ollama fallback failed: {ollama_exc}")

        logger.error(f"Generation failed (all retries exhausted): {str(e)}")
        return f"Generation Error: {str(e)[:200]}"