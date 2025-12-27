"""
Language Detection and Translation Service for Kuapa AI
Supports: English, Twi, Ga, Ewe, Dagbani

Features:
- Text-based language detection
- Translation between English and Ghanaian languages
- Bilingual response system
"""

import re
from typing import Optional, Dict, Tuple
from .logger import logger

try:
    from googletrans import Translator
    _HAS_TRANSLATOR = True
except ImportError:
    _HAS_TRANSLATOR = False
    logger.warning("googletrans not installed - translation features disabled")

# Language configurations
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'tw': 'Twi (Akan)',
    'ga': 'Ga',
    'ee': 'Ewe',
    'dag': 'Dagbani'
}

# Google Translate language codes mapping
GOOGLE_TRANSLATE_CODES = {
    'en': 'en',
    'tw': 'ak',  # Akan (includes Twi)
    'ga': 'gaa',  # Ga
    'ee': 'ee',   # Ewe
    'dag': 'dag'  # Dagbani
}

# Common words/phrases for language detection
LANGUAGE_PATTERNS = {
    'tw': {
        # Twi-specific characters
        'chars': ['ɔ', 'ɛ', 'ŋ'],
        
        # Common Twi words
        'words': [
            'yɛ', 'wo', 'na', 'ne', 'aka', 'adɛn', 'ɛte', 'sɛn', 'dɛn',
            'mepaakyɛw', 'medaase', 'ɛyɛ', 'deɛ', 'nhwɛ', 'ɔkasa', 'kasa',
            'aboa', 'afuom', 'nsuo', 'kuayɛ', 'mfuo', 'atɔ', 'tɔn',
            'mepawo', 'wo ho te sɛn', 'ma me', 'sɛdeɛ', 'yɛbɛyɛ',
            'waye', 'ɔyɛ', 'ɔde', 'ɔbɛ', 'ɔrepe', 'ɔmpɛ'
        ],
        
        # Twi agricultural terms
        'agriculture': [
            'afuom', 'kuayɛ', 'mfuo', 'aboa', 'nnɔbae', 'abɔdeɛ',
            'aburo', 'aburoo', 'bankye', 'bayerɛ', 'nkruma', 'mako'
        ]
    },
    
    'ga': {
        'chars': ['ɛ', 'ɔ', 'ŋ'],
        'words': [
            'ni', 'ke', 'tsɛ', 'le', 'kɛ', 'mli', 'shwɛ', 'mi', 'ni',
            'ɔyɛ', 'he', 'kome', 'nitsumɔ', 'oyiwala', 'afɛmɔ', 'yao'
        ]
    },
    
    'ee': {
        'chars': ['ɖ', 'ɛ', 'ɔ', 'ŋ', 'ʋ'],
        'words': [
            'nye', 'wò', 'ɖe', 'le', 'na', 'ŋu', 'wo', 'be', 'ɖi',
            'mía', 'esia', 'akpɔ', 'di', 'vu', 'ɖo'
        ]
    },
    
    'dag': {
        'chars': ['ŋ', 'ɣ'],
        'words': [
            'n', 'ka', 'be', 'ni', 'ti', 'di', 'la', 'bi', 'o', 'a',
            'daa', 'paa', 'yɛ', 'kum', 'nam', 'buɣu'
        ]
    }
}

class LanguageService:
    """Service for language detection and translation"""
    
    def __init__(self):
        """Initialize translator if available"""
        self.translator = None
        if _HAS_TRANSLATOR:
            try:
                self.translator = Translator()
                logger.info("Google Translator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize translator: {e}")
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of input text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (language_code, confidence_score)
            
        Example:
            >>> detect_language("Wo ho te sɛn?")
            ('tw', 0.85)
        """
        if not text or len(text.strip()) < 3:
            return 'en', 0.5
        
        text_lower = text.lower().strip()
        
        # Try pattern-based detection first (more accurate for Ghanaian languages)
        pattern_result = self._pattern_based_detection(text_lower)
        if pattern_result[1] >= 0.6:  # High confidence from patterns
            logger.info(f"Language detected (pattern): {pattern_result[0]} (confidence: {pattern_result[1]:.2f})")
            return pattern_result
        
        # Try Google Translate detection as fallback
        if self.translator:
            try:
                detection = self.translator.detect(text)
                detected_lang = detection.lang
                confidence = detection.confidence if hasattr(detection, 'confidence') else 0.8
                
                # Map Google's codes to our codes
                lang_code = self._map_google_lang_code(detected_lang)
                
                logger.info(f"Language detected (Google): {lang_code} (confidence: {confidence:.2f})")
                return lang_code, confidence
                
            except Exception as e:
                logger.warning(f"Google Translate detection failed: {e}")
        
        # Fallback to pattern detection with lower confidence
        logger.info(f"Language detected (fallback): {pattern_result[0]} (confidence: {pattern_result[1]:.2f})")
        return pattern_result
    
    def _pattern_based_detection(self, text: str) -> Tuple[str, float]:
        """
        Detect language using pattern matching
        Returns (language_code, confidence_score)
        """
        scores = {}
        
        for lang_code, patterns in LANGUAGE_PATTERNS.items():
            score = 0.0
            total_checks = 0
            
            # Check for special characters (strong indicator)
            char_matches = sum(1 for char in patterns['chars'] if char in text)
            if char_matches > 0:
                score += char_matches * 0.3
                total_checks += len(patterns['chars'])
            
            # Check for common words
            word_matches = sum(1 for word in patterns['words'] 
                             if re.search(r'\b' + re.escape(word) + r'\b', text))
            if word_matches > 0:
                score += word_matches * 0.15
                total_checks += min(len(patterns['words']), 10)
            
            # Check agricultural terms if available
            if 'agriculture' in patterns:
                agri_matches = sum(1 for word in patterns['agriculture']
                                 if re.search(r'\b' + re.escape(word) + r'\b', text))
                if agri_matches > 0:
                    score += agri_matches * 0.2
                    total_checks += min(len(patterns['agriculture']), 5)
            
            # Normalize score
            if total_checks > 0:
                normalized_score = min(score, 1.0)
                scores[lang_code] = normalized_score
            else:
                scores[lang_code] = 0.0
        
        # Get language with highest score
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])
            if best_lang[1] > 0.1:  # Minimum threshold
                return best_lang
        
        # Default to English with low confidence
        return 'en', 0.3
    
    def _map_google_lang_code(self, google_code: str) -> str:
        """Map Google Translate language codes to our codes"""
        code_mapping = {
            'en': 'en',
            'ak': 'tw',  # Akan -> Twi
            'tw': 'tw',  # Sometimes Google uses 'tw' directly
            'gaa': 'ga',
            'ee': 'ee',
            'dag': 'dag'
        }
        return code_mapping.get(google_code, 'en')
    
    def translate_to_english(self, text: str, source_lang: str = 'auto') -> Dict[str, str]:
        """
        Translate text to English
        
        Args:
            text: Text to translate
            source_lang: Source language code (or 'auto' for detection)
            
        Returns:
            Dict with 'text' (translated), 'source_lang', 'confidence'
        """
        if not text:
            return {'text': '', 'source_lang': 'en', 'confidence': 0.0}
        
        # If already English, return as-is
        if source_lang == 'en':
            return {'text': text, 'source_lang': 'en', 'confidence': 1.0}
        
        if not self.translator:
            logger.warning("Translator not available, returning original text")
            return {'text': text, 'source_lang': source_lang, 'confidence': 0.0}
        
        try:
            # Detect language if needed
            if source_lang == 'auto':
                detected_lang, confidence = self.detect_language(text)
                source_lang = detected_lang
            else:
                confidence = 0.8
            
            # If detected as English, no translation needed
            if source_lang == 'en':
                return {'text': text, 'source_lang': 'en', 'confidence': confidence}
            
            # Translate to English
            google_lang = GOOGLE_TRANSLATE_CODES.get(source_lang, source_lang)
            translation = self.translator.translate(text, src=google_lang, dest='en')
            
            logger.info(f"Translated from {source_lang} to en: '{text[:50]}...' -> '{translation.text[:50]}...'")
            
            return {
                'text': translation.text,
                'source_lang': source_lang,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Translation to English failed: {e}")
            return {'text': text, 'source_lang': source_lang, 'confidence': 0.0}
    
    def translate_from_english(self, text: str, target_lang: str) -> Dict[str, str]:
        """
        Translate English text to target language
        
        Args:
            text: English text to translate
            target_lang: Target language code (tw, ga, ee, dag)
            
        Returns:
            Dict with 'text' (translated), 'target_lang', 'success'
        """
        if not text:
            return {'text': '', 'target_lang': target_lang, 'success': False}
        
        # If target is English, return as-is
        if target_lang == 'en':
            return {'text': text, 'target_lang': 'en', 'success': True}
        
        if not self.translator:
            logger.warning("Translator not available, returning original text")
            return {'text': text, 'target_lang': target_lang, 'success': False}
        
        try:
            google_lang = GOOGLE_TRANSLATE_CODES.get(target_lang, target_lang)
            translation = self.translator.translate(text, src='en', dest=google_lang)
            
            logger.info(f"Translated from en to {target_lang}: '{text[:50]}...' -> '{translation.text[:50]}...'")
            
            return {
                'text': translation.text,
                'target_lang': target_lang,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Translation to {target_lang} failed: {e}")
            return {'text': text, 'target_lang': target_lang, 'success': False}
    
    def create_bilingual_response(
        self, 
        english_text: str, 
        target_lang: str,
        include_english: bool = True
    ) -> str:
        """
        Create a bilingual response (both English and target language)
        
        Args:
            english_text: Response in English
            target_lang: Target language for translation
            include_english: Whether to include English version
            
        Returns:
            Bilingual formatted response
        """
        if target_lang == 'en':
            return english_text
        
        # Translate to target language
        translation = self.translate_from_english(english_text, target_lang)
        
        if translation['success'] and include_english:
            # Return both versions
            lang_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang.upper())
            return f"{translation['text']}\n\n[English: {english_text}]"
        elif translation['success']:
            # Return only translation
            return translation['text']
        else:
            # Translation failed, return English only
            return english_text


# Singleton instance
_language_service = None

def get_language_service() -> LanguageService:
    """Get or create language service singleton"""
    global _language_service
    if _language_service is None:
        _language_service = LanguageService()
    return _language_service


# Convenience functions
def detect_language(text: str) -> Tuple[str, float]:
    """Detect language of text"""
    return get_language_service().detect_language(text)

def translate_to_english(text: str, source_lang: str = 'auto') -> Dict[str, str]:
    """Translate text to English"""
    return get_language_service().translate_to_english(text, source_lang)

def translate_from_english(text: str, target_lang: str) -> Dict[str, str]:
    """Translate English to target language"""
    return get_language_service().translate_from_english(text, target_lang)

def is_supported_language(lang_code: str) -> bool:
    """Check if language code is supported"""
    return lang_code in SUPPORTED_LANGUAGES
