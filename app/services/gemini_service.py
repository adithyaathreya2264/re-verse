"""
Google Gemini API service for LLM script generation and TTS.
Handles PDF analysis and multi-speaker dialogue creation.
"""
import json
from typing import Dict, List, Optional
import google.generativeai as genai

from app.core.config import settings
from app.models.enums import StyleType, DurationType
from app.utils.logger import logger


# ==================== Initialize Gemini API ====================

def initialize_gemini():
    """Initialize Gemini API with API key."""
    try:
        genai.configure(api_key=settings.google_api_key)
        logger.info("✅ Gemini API initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini API: {e}")
        raise


# Initialize on module import
initialize_gemini()


# ==================== PDF Text Extraction ====================

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text content from PDF bytes.
    
    Args:
        pdf_bytes: PDF file contents as bytes
        
    Returns:
        Extracted text as string
        
    Raises:
        Exception: If PDF parsing fails
    """
    try:
        import PyPDF2
        import io
        
        logger.info("📄 Extracting text from PDF...")
        
        # Create PDF reader from bytes
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text_content = []
        total_pages = len(pdf_reader.pages)
        
        for page_num in range(total_pages):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            text_content.append(text)
        
        full_text = "\n\n".join(text_content)
        logger.info(f"✅ Extracted {len(full_text)} characters from {total_pages} pages")
        
        return full_text
        
    except Exception as e:
        logger.error(f"❌ PDF extraction failed: {e}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


# ==================== Script Generation ====================

def build_script_generation_prompt(
    pdf_text: str,
    user_prompt: str,
    style: str,
    duration: str
) -> str:
    """Build the system prompt for script generation."""
    style_enum = StyleType(style)
    style_instructions = style_enum.get_system_prompt_modifier()
    
    duration_enum = DurationType(duration)
    estimated_time = duration_enum.get_estimated_minutes()
    
    # Get configuration from settings
    max_turns = settings.get_dialogue_turns(duration)
    char_limit = settings.get_pdf_char_limit(duration)
    
    prompt = f"""You are a podcast script writer. Create a concise, engaging dialogue.

**DOCUMENT (Limited to {char_limit} chars):**
{pdf_text[:char_limit]}

**USER FOCUS:**
{user_prompt}

**STYLE:**
{style_instructions}

**TARGET:** ~{estimated_time} of audio

**STRICT REQUIREMENTS:**
1. Generate EXACTLY {max_turns} dialogue turns
2. Each text: Maximum 2 short sentences
3. Output ONLY valid JSON (no markdown, no explanations)
4. Keep very concise

**JSON FORMAT:**
{{
  "title": "Brief engaging title",
  "speakers": [
    {{"id": "speaker1", "name": "Alex", "role": "Host"}},
    {{"id": "speaker2", "name": "Sam", "role": "Expert"}}
  ],
  "dialogue": [
    {{"speaker": "speaker1", "text": "Brief opening."}},
    {{"speaker": "speaker2", "text": "Concise response."}}
  ]
}}

Generate exactly {max_turns} dialogue turns now:"""
    
    return prompt

async def generate_script_from_pdf(
    pdf_bytes: bytes,
    user_prompt: str,
    style: str,
    duration: str
) -> Dict:
    """
    Generate podcast script from PDF using configured AI provider.
    
    Automatically selects between Groq (Llama 3.1) and Gemini.
    """
    try:
        # Extract text from PDF first
        pdf_text = extract_text_from_pdf(pdf_bytes)
        
        if not pdf_text or len(pdf_text.strip()) < 100:
            raise Exception("PDF contains insufficient text content")
        
        # Choose provider based on configuration
        if settings.ai_provider == "groq" and settings.groq_api_key:
            logger.info("Using Groq (Llama 3.1) for script generation")
            from app.services.groq_service import generate_script_with_groq
            return await generate_script_with_groq(pdf_text, user_prompt, style, duration)
        else:
            logger.info("Using Gemini for script generation")
            return await generate_script_with_gemini(pdf_text, user_prompt, style, duration)
            
    except Exception as e:
        logger.error(f"❌ Script generation failed: {e}")
        raise Exception(f"Failed to generate script: {str(e)}")


async def generate_script_from_pdf(
    pdf_bytes: bytes,
    user_prompt: str,
    style: str,
    duration: str
) -> Dict:
    """
    Generate podcast script from PDF using configured AI provider.
    
    Automatically selects between Groq (Llama 3.1) and Gemini.
    """
    try:
        # Extract text from PDF first
        pdf_text = extract_text_from_pdf(pdf_bytes)
        
        if not pdf_text or len(pdf_text.strip()) < 100:
            raise Exception("PDF contains insufficient text content")
        
        # Choose provider based on configuration
        if settings.ai_provider == "groq" and settings.groq_api_key:
            logger.info("Using Groq (Llama 3.1) for script generation")
            from app.services.groq_service import generate_script_with_groq
            return await generate_script_with_groq(pdf_text, user_prompt, style, duration)
        else:
            logger.info("Using Gemini for script generation")
            return await generate_script_with_gemini(pdf_text, user_prompt, style, duration)
            
    except Exception as e:
        logger.error(f"❌ Script generation failed: {e}")
        raise Exception(f"Failed to generate script: {str(e)}")


async def generate_script_with_gemini(
    pdf_text: str,
    user_prompt: str,
    style: str,
    duration: str
) -> Dict:
    """Original Gemini implementation (fallback)."""
    # Your existing Gemini code here
    # ... (keep the old implementation)



def parse_script_json(response_text: str) -> Dict:
    """Parse JSON with aggressive repair for truncated responses."""
    import re
    
    try:
        text = response_text.strip()
        
        # Remove markdown
        text = re.sub(r'``````', '', text)
        
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Repair truncated JSON
        logger.warning("Attempting JSON repair...")
        
        # Find last complete dialogue entry
        last_complete = text.rfind('"}')
        if last_complete == -1:
            raise Exception("No complete dialogue entries found")
        
        # Truncate to last complete entry
        repaired = text[:last_complete + 2]
        
        # Count brackets
        open_brackets = repaired.count('[') - repaired.count(']')
        open_braces = repaired.count('{') - repaired.count('}')
        
        # Close arrays
        if open_brackets > 0:
            if '"dialogue"' in repaired and repaired.rfind('[') > repaired.rfind(']'):
                repaired += '\n  ]'
                open_brackets -= 1
            repaired += ']' * open_brackets
        
        # Close objects
        repaired += '}' * open_braces
        
        # Try parsing repaired JSON
        return json.loads(repaired)
        
    except Exception as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Text preview: {response_text[:500]}")
        raise Exception("Could not parse script JSON")


def validate_script_structure(script: Dict) -> None:
    """Validate that the script has the required structure."""
    required_keys = ["title", "speakers", "dialogue"]
    
    for key in required_keys:
        if key not in script:
            raise Exception(f"Script missing required key: {key}")
    
    if not isinstance(script["speakers"], list) or len(script["speakers"]) < 2:
        raise Exception("Script must have at least 2 speakers")
    
    if not isinstance(script["dialogue"], list) or len(script["dialogue"]) < 5:
        raise Exception("Script must have at least 5 dialogue turns")
    
    # Validate speaker references
    speaker_ids = {s["id"] for s in script["speakers"]}
    for turn in script["dialogue"]:
        if turn["speaker"] not in speaker_ids:
            raise Exception(f"Invalid speaker reference: {turn['speaker']}")
    
    logger.info("✅ Script structure validated")


# ==================== Multi-Speaker Audio Generation ====================

def format_dialogue_for_tts(script_data: Dict) -> str:
    """Format the script dialogue into text for TTS."""
    try:
        speakers = {s["id"]: s["name"] for s in script_data["speakers"]}
        formatted_lines = []
        
        for turn in script_data["dialogue"]:
            speaker_name = speakers[turn["speaker"]]
            text = turn["text"]
            formatted_lines.append(f"[{speaker_name}]: {text}")
        
        return "\n\n".join(formatted_lines)
        
    except Exception as e:
        logger.error(f"Error formatting dialogue: {e}")
        raise


async def generate_audio_from_script(script_data: Dict) -> bytes:
    """
    Generate multi-speaker audio from script using Gemini TTS.
    
    Args:
        script_data: Script dictionary with speakers and dialogue
        
    Returns:
        Audio file contents as bytes (MP3 format)
        
    Raises:
        Exception: If audio generation fails
    """
    try:
        logger.info("🎙️ Generating multi-speaker audio with Gemini TTS...")
        
        # For now, return placeholder
        # TODO: Implement actual TTS when Gemini native audio is available
        logger.warning("⚠️ TTS not fully implemented - generating placeholder")
        
        # Create a minimal MP3 file (silence)
        # In production, this would call Gemini TTS
        placeholder_audio = b'\xff\xfb\x90\x00' * 1000  # Minimal MP3 header pattern
        
        return placeholder_audio
        
    except Exception as e:
        logger.error(f"❌ Audio generation failed: {e}")
        raise Exception(f"Failed to generate audio: {str(e)}")
