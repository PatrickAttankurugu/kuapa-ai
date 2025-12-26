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
    Transcribe audio file using Google Gemini
    
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
        
        # Create prompt based on language
        if language and language in SUPPORTED_LANGUAGES:
            prompt = f"""Transcribe this audio recording. The speaker is speaking in {SUPPORTED_LANGUAGES[language]}.

Instructions:
1. Transcribe exactly what is said in the audio
2. If speaking {SUPPORTED_LANGUAGES[language]}, transcribe in that language
3. If you cannot understand the audio, respond with: "Could not transcribe audio"
4. Only return the transcribed text, nothing else

Transcription:"""
        else:
            prompt = """Transcribe this audio recording. Detect the language automatically.

The audio may be in one of these languages:
- English
- Twi (Akan)
- Ga
- Ewe
- Dagbani

Instructions:
1. Detect the language being spoken
2. Transcribe exactly what is said
3. If you cannot understand the audio, respond with: "Could not transcribe audio"
4. Only return the transcribed text, nothing else

Transcription:"""
        
        # Use Gemini to transcribe
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        logger.info("Sending audio to Gemini for transcription...")
        response = model.generate_content(
            [prompt, audio_file],
            request_options={"timeout": 120}
        )
        
        transcribed_text = response.text.strip()
        
        # Detect language from text if not specified
        detected_language = language or await _detect_language(transcribed_text)
        
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
        
        if not transcribed_text or transcribed_text == "Could not transcribe audio":
            logger.warning("Transcription failed or returned empty")
            return {
                "text": "",
                "language": detected_language,
                "error": "Could not transcribe audio"
            }
        
        logger.info(f"Transcription successful: {transcribed_text[:100]}...")
        logger.info(f"Detected language: {detected_language}")
        
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


async def _convert_audio_if_needed(audio_path: str) -> str:
    """
    Convert audio to WAV format if needed
    Gemini supports: WAV, MP3, AIFF, AAC, OGG, FLAC
    """
    file_ext = Path(audio_path).suffix.lower()
    
    # These formats are directly supported
    supported_formats = ['.wav', '.mp3', '.aiff', '.aac', '.ogg', '.flac', '.m4a']
    
    if file_ext in supported_formats:
        logger.info(f"Audio format {file_ext} is supported, no conversion needed")
        return audio_path
    
    try:
        logger.info(f"Converting audio from {file_ext} to WAV...")
        
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


async def _detect_language(text: str) -> str:
    """
    Detect language from transcribed text using simple heuristics
    """
    if not text:
        return "en"
    
    text_lower = text.lower()
    
    # Simple keyword-based detection for Ghanaian languages
    twi_keywords = ['me', 'wo', 'ɔ', 'ɛ', 'ne', 'na', 'yɛ', 'aka', 'adɛn']
    ga_keywords = ['ni', 'ke', 'tsɛ', 'le', 'kɛ']
    ewe_keywords = ['nye', 'wò', 'ɖe', 'le', 'na']
    
    # Count matches
    twi_count = sum(1 for keyword in twi_keywords if keyword in text_lower)
    ga_count = sum(1 for keyword in ga_keywords if keyword in text_lower)
    ewe_count = sum(1 for keyword in ewe_keywords if keyword in text_lower)
    
    # Return language with most matches
    if twi_count > ga_count and twi_count > ewe_count and twi_count > 0:
        return "tw"
    elif ga_count > ewe_count and ga_count > 0:
        return "ga"
    elif ewe_count > 0:
        return "ee"
    else:
        return "en"  # Default to English


# Legacy function for backward compatibility
async def transcribe_wav(path: str) -> Dict[str, str]:
    """
    Legacy function - redirects to transcribe_audio
    """
    return await transcribe_audio(path)
