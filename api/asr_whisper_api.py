import os
import time
import tempfile
from pathlib import Path
from typing import Dict, Optional
import google.generativeai as genai
from pydub import AudioSegment
from .logger import logger
from .config import GEMINI_API_KEY

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Supported languages for transcription
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'tw': 'Twi (Akan)',
    'ga': 'Ga',
    'ee': 'Ewe',
    'dag': 'Dagbani'
}

async def transcribe_audio(audio_path: str, language: Optional[str] = None) -> Dict[str, str]:
    """
    Transcribe audio file using Google Gemini with improved language detection
    
    Args:
        audio_path: Path to audio file (.ogg, .mp3, .wav, etc.)
        language: Target language code (en, tw, etc.). Auto-detect if None
    
    Returns:
        Dict with 'text' (transcribed text) and 'language' (detected/specified language)
    """
    
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not configured - cannot transcribe audio")
        return {"text": "", "language": "en", "error": "Gemini API not configured"}
    
    try:
        logger.info(f"Starting audio transcription: {audio_path}")
        
        # Convert audio to supported format if needed
        audio_file_path = await _convert_audio_if_needed(audio_path)
        
        # Upload audio file to Gemini
        logger.info("Uploading audio file to Gemini...")
        audio_file = genai.upload_file(path=audio_file_path)
        
        # Wait for file to be processed
        max_wait = 30  # seconds
        wait_time = 0
        while audio_file.state.name == "PROCESSING" and wait_time < max_wait:
            time.sleep(1)
            wait_time += 1
            audio_file = genai.get_file(audio_file.name)
        
        if audio_file.state.name == "FAILED":
            raise RuntimeError("Audio file processing failed")
        
        logger.info("Audio file uploaded successfully")
        
        # Create prompt with improved language detection
        if language and language in SUPPORTED_LANGUAGES:
            prompt = f"""Transcribe this audio recording. The speaker is speaking in {SUPPORTED_LANGUAGES[language]}.

Instructions:
1. Listen carefully and transcribe exactly what is said
2. Transcribe in {SUPPORTED_LANGUAGES[language]} using proper spelling
3. If you cannot understand the audio clearly, respond with: "TRANSCRIPTION_FAILED"
4. Return ONLY the transcribed text, nothing else
5. Do not add any explanations or notes

Transcription:"""
        else:
            # Auto-detect language with explicit format
            prompt = """Transcribe this audio recording and detect the language.

The speaker may be using one of these languages:
- English
- Twi (Akan) - a Ghanaian language
- Ga - a Ghanaian language
- Ewe - a Ghanaian language  
- Dagbani - a Ghanaian language

Respond in this EXACT format:
LANGUAGE: [language code: en, tw, ga, ee, or dag]
TRANSCRIPTION: [exact transcription in the detected language]

Instructions:
1. Detect which language is being spoken
2. Transcribe exactly what is said in that language
3. Use proper spelling for the detected language
4. Follow the format above EXACTLY
5. If you cannot understand the audio, write:
   LANGUAGE: en
   TRANSCRIPTION: TRANSCRIPTION_FAILED

Audio transcription:"""
        
        # Use Gemini to transcribe
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        logger.info("Sending audio to Gemini for transcription...")
        response = model.generate_content(
            [prompt, audio_file],
            request_options={"timeout": 120}
        )
        
        response_text = response.text.strip()
        
        # Parse response
        if language:
            # If language was specified, use it
            transcribed_text = response_text
            detected_language = language
        else:
            # Parse the structured response
            detected_language, transcribed_text = _parse_transcription_response(response_text)
        
        # Clean up uploaded file from Gemini
        try:
            genai.delete_file(audio_file.name)
            logger.info("Cleaned up uploaded file from Gemini")
        except Exception as e:
            logger.warning(f"Failed to delete file from Gemini: {e}")
        
        # Clean up temporary converted file if it was created
        if audio_file_path != audio_path:
            try:
                os.remove(audio_file_path)
                logger.info("Cleaned up temporary converted audio file")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")
        
        # Check for transcription failure
        if not transcribed_text or transcribed_text == "TRANSCRIPTION_FAILED":
            logger.warning("Transcription failed or returned empty")
            return {
                "text": "",
                "language": detected_language,
                "error": "Could not transcribe audio clearly"
            }
        
        logger.info(f"Transcription successful: {transcribed_text[:100]}...")
        logger.info(f"Detected language: {detected_language} ({SUPPORTED_LANGUAGES.get(detected_language, 'Unknown')})")
        
        return {
            "text": transcribed_text,
            "language": detected_language
        }
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
        return {
            "text": "",
            "language": language or "en",
            "error": str(e)
        }


def _parse_transcription_response(response_text: str) -> tuple[str, str]:
    """
    Parse the structured transcription response from Gemini
    
    Returns:
        Tuple of (language_code, transcribed_text)
    """
    try:
        lines = response_text.strip().split('\n')
        language_code = "en"  # Default
        transcription = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith("LANGUAGE:"):
                lang_part = line.replace("LANGUAGE:", "").strip().lower()
                # Extract just the language code
                if lang_part in SUPPORTED_LANGUAGES:
                    language_code = lang_part
                else:
                    # Try to extract code from longer string
                    for code in SUPPORTED_LANGUAGES.keys():
                        if code in lang_part:
                            language_code = code
                            break
            elif line.startswith("TRANSCRIPTION:"):
                transcription = line.replace("TRANSCRIPTION:", "").strip()
        
        # If we didn't find the structured format, treat entire response as transcription
        if not transcription:
            transcription = response_text
            # Try simple keyword detection as fallback
            language_code = _simple_language_detection(response_text)
        
        return language_code, transcription
    
    except Exception as e:
        logger.warning(f"Error parsing transcription response: {e}")
        # Fallback: use simple detection
        return _simple_language_detection(response_text), response_text


def _simple_language_detection(text: str) -> str:
    """
    Simple keyword-based language detection as fallback
    """
    if not text:
        return "en"
    
    text_lower = text.lower()
    
    # Twi-specific characters and common words
    if any(char in text for char in ['ɔ', 'ɛ', 'ŋ']):
        return "tw"
    
    # Common Twi words
    twi_words = ['yɛ', 'wo', 'na', 'ne', 'aka', 'adɛn', 'ɛte', 'sɛn', 'dɛn', 'mepaakyɛw']
    twi_count = sum(1 for word in twi_words if word in text_lower)
    
    # Common Ga words
    ga_words = ['ni', 'ke', 'tsɛ', 'le', 'kɛ', 'mli', 'shwɛ']
    ga_count = sum(1 for word in ga_words if word in text_lower)
    
    # Common Ewe words  
    ewe_words = ['nye', 'wò', 'ɖe', 'le', 'na', 'ŋu', 'wo']
    ewe_count = sum(1 for word in ewe_words if word in text_lower)
    
    # Common Dagbani words
    dag_words = ['n', 'ka', 'be', 'ni', 'ti', 'di', 'la']
    dag_count = sum(1 for word in dag_words if word in text_lower)
    
    # Return language with most matches (with threshold)
    max_count = max(twi_count, ga_count, ewe_count, dag_count)
    
    if max_count >= 2:  # Need at least 2 matches to be confident
        if twi_count == max_count:
            return "tw"
        elif ga_count == max_count:
            return "ga"
        elif ewe_count == max_count:
            return "ee"
        elif dag_count == max_count:
            return "dag"
    
    return "en"  # Default to English


async def _convert_audio_if_needed(audio_path: str) -> str:
    """
    Convert audio to WAV format if needed
    WhatsApp sends OGG Opus which Gemini doesn't support well - always convert to WAV
    Gemini officially supports: WAV, MP3, AIFF, AAC, FLAC
    """
    file_ext = Path(audio_path).suffix.lower()
    
    # Always convert OGG files (WhatsApp voice messages) to WAV
    # because Gemini has issues with OGG Opus codec
    if file_ext == '.ogg':
        logger.info(f"Converting OGG to WAV (Gemini doesn't support OGG Opus well)...")
    # These formats work directly with Gemini
    elif file_ext in ['.wav', '.mp3', '.aiff', '.aac', '.flac']:
        logger.info(f"Audio format {file_ext} is supported, no conversion needed")
        return audio_path
    else:
        logger.info(f"Converting audio from {file_ext} to WAV...")
    
    try:
        # Load audio file
        audio = AudioSegment.from_file(audio_path)
        
        # Create temporary WAV file
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_wav_path = temp_wav.name
        temp_wav.close()
        
        # Export as WAV
        audio.export(temp_wav_path, format='wav')
        
        logger.info(f"Audio converted successfully to: {temp_wav_path}")
        return temp_wav_path
        
    except Exception as e:
        logger.error(f"Error converting audio: {str(e)}")
        # Return original path if conversion fails
        return audio_path


# Legacy function for backward compatibility
async def transcribe_wav(path: str) -> Dict[str, str]:
    """
    Legacy function - redirects to transcribe_audio
    """
    return await transcribe_audio(path)
