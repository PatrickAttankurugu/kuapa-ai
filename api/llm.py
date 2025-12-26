import os
from typing import List, Tuple
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

async def answer(query: str, context_chunks: List[Tuple[str, float, str]]) -> str:
    """
    Generate an answer using Google Gemini 2.5 Flash based on the query and context.

    Args:
        query: User's question
        context_chunks: List of (content, score, source) tuples from RAG retrieval

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

        # Create the full prompt
        full_prompt = f"""{SYSTEM_PROMPT}

Question: {query}

Context:
{context_text}

Answer in under 180 tokens, providing practical and accurate agricultural advice."""

        # Generate response (synchronous API, but wrapped in async function)
        response = model.generate_content(full_prompt)

        return response.text.strip()

    except Exception as e:
        return f"Sorry, I encountered an error generating a response: {str(e)}"
