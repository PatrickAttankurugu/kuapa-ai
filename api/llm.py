import os
from typing import List, Tuple, Optional
from .config import GEMINI_API_KEY, GEMINI_MODEL, LLM_TEMPERATURE

try:
    import google.generativeai as genai
    _HAS_GEMINI = True
except Exception:
    _HAS_GEMINI = False

SYSTEM_PROMPT = (
    "You are Kuapa AI, an agricultural advisor for Ghanaian farmers. "
    "Answer concisely and practically. If unsure, acknowledge uncertainty. "
    "Never hallucinate facts. Use provided context for accurate advice."
)

# Language-specific system prompts
LANGUAGE_PROMPTS = {
    "en": "Respond in English.",
    "tw": "Respond in Twi (Akan language). Use Twi vocabulary and grammar.",
    "ga": "Respond in Ga language. Use Ga vocabulary and grammar.",
    "ee": "Respond in Ewe language. Use Ewe vocabulary and grammar.",
    "dag": "Respond in Dagbani language. Use Dagbani vocabulary and grammar."
}

LANGUAGE_NAMES = {
    "en": "English",
    "tw": "Twi",
    "ga": "Ga",
    "ee": "Ewe",
    "dag": "Dagbani"
}

async def answer(query: str, context_chunks: List[Tuple[str, float, str]], language: Optional[str] = None) -> str:
    """
    Generate an answer using Google Gemini 2.5 Flash based on the query and context.

    Args:
        query: User's question
        context_chunks: List of (content, score, source) tuples from RAG retrieval
        language: Language code for response (en, tw, ga, ee, dag). Auto-detect if None.

    Returns:
        Generated answer string
    """
    if not _HAS_GEMINI:
        return "Sorry, Gemini AI library is not installed."

    if not GEMINI_API_KEY:
        return "Sorry, I'm currently not configured for LLM responses. Please set GEMINI_API_KEY."

    try:
        # Configure Gemini
        genai.configure(api_key=GEMINI_API_KEY)

        # Create the model
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": LLM_TEMPERATURE,
                "max_output_tokens": 256,
                "top_p": 0.95,
            }
        )

        # Build context from retrieved chunks
        context_text = "\n\n".join([f"[source: {s}] {c}" for c, _, s in context_chunks])

        # Get language instruction
        language_code = language or "en"
        language_instruction = LANGUAGE_PROMPTS.get(language_code, LANGUAGE_PROMPTS["en"])
        language_name = LANGUAGE_NAMES.get(language_code, "English")

        # Create the full prompt
        full_prompt = f"""{SYSTEM_PROMPT}

{language_instruction}

Question (may be in {language_name}): {query}

Context:
{context_text}

Provide a practical and accurate answer in {language_name}, using simple language that farmers can understand. Keep the response under 180 tokens."""

        # Generate response (synchronous API, but wrapped in async function)
        response = model.generate_content(full_prompt)

        return response.text.strip()

    except Exception as e:
        # Provide error message in appropriate language
        error_messages = {
            "en": f"Sorry, I encountered an error generating a response: {str(e)}",
            "tw": f"Kosɛ, manya haw wɔ mmuae a mede reba no mu: {str(e)}",
            "ga": f"Afɛmɔ, mi kɛ hiaŋ lɛ ni nitsumɔi lɛ: {str(e)}",
            "ee": f"Miɖe kuku, mekpɔ kuxi aɖe le ŋuɖoɖo nam me: {str(e)}",
            "dag": f"N paai, n nya zuɣu: {str(e)}"
        }
        
        language_code = language or "en"
        return error_messages.get(language_code, error_messages["en"])
