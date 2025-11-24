"""
Groq API service for LLM script generation using Llama 3.1.
Fast, free, and reliable alternative to Gemini.
"""
import json
from typing import Dict
from groq import Groq

from app.core.config import settings
from app.models.enums import StyleType, DurationType
from app.utils.logger import logger


# Initialize Groq client
try:
    client = Groq(api_key=settings.groq_api_key)
    logger.info("✅ Groq API initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Groq API: {e}")
    client = None


def build_groq_prompt(
    pdf_text: str,
    user_prompt: str,
    style: str,
    duration: str
) -> tuple[str, str]:
    """
    Build system and user prompts for Groq.
    
    Returns:
        (system_prompt, user_message)
    """
    style_enum = StyleType(style)
    style_instructions = style_enum.get_system_prompt_modifier()
    
    duration_enum = DurationType(duration)
    estimated_time = duration_enum.get_estimated_minutes()
    
    max_turns = settings.get_dialogue_turns(duration)
    char_limit = settings.get_pdf_char_limit(duration)
    
    system_prompt = f"""You are an expert podcast script writer. Create engaging, natural dialogues for educational podcasts.

STYLE: {style_instructions}

OUTPUT RULES:
1. Generate EXACTLY {max_turns} dialogue exchanges
2. Each speaker text: 1-3 sentences maximum
3. Output ONLY valid JSON (no markdown, no explanations)
4. Make conversation natural and engaging
5. Focus on the content provided by the user

JSON STRUCTURE:
{{
  "title": "Engaging episode title (max 60 chars)",
  "speakers": [
    {{"id": "speaker1", "name": "Host Name", "role": "Brief role"}},
    {{"id": "speaker2", "name": "Expert Name", "role": "Brief role"}}
  ],
  "dialogue": [
    {{"speaker": "speaker1", "text": "Opening question or statement"}},
    {{"speaker": "speaker2", "text": "Response with information"}}
  ]
}}"""

    user_message = f"""Create a {max_turns}-turn podcast dialogue about the following content:

**DOCUMENT EXCERPT (first {char_limit} characters):**
{pdf_text[:char_limit]}

**USER FOCUS:**
{user_prompt}

**TARGET DURATION:** Approximately {estimated_time}

Generate the podcast script as valid JSON with exactly {max_turns} dialogue turns:"""
    
    return system_prompt, user_message


async def generate_script_with_groq(
    pdf_text: str,
    user_prompt: str,
    style: str,
    duration: str
) -> Dict:
    """
    Generate podcast script using Groq's Llama 3.1 model.
    
    Args:
        pdf_text: Extracted PDF text
        user_prompt: User's focus instructions
        style: Conversation style
        duration: Duration preference
        
    Returns:
        Dictionary containing script data
        
    Raises:
        Exception: If generation fails
    """
    try:
        if not client:
            raise Exception("Groq client not initialized. Check GROQ_API_KEY in .env")
        
        logger.info("🤖 Generating script with Groq (Llama 3.1 70B)...")
        
        # Build prompts
        system_prompt, user_message = build_groq_prompt(
            pdf_text, user_prompt, style, duration
        )
        
        # Get token limit
        max_tokens = settings.get_duration_tokens(duration)
        
        logger.info(f"📝 Calling Groq API (model: llama-3.1-70b-versatile, max_tokens={max_tokens})...")
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # or "llama-3.1-8b-instant" for speed
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=max_tokens,
            top_p=0.95,
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        # Extract response
        script_text = response.choices[0].message.content
        
        if not script_text:
            raise Exception("Groq API returned empty response")
        
        logger.info(f"✅ Received response: {len(script_text)} characters")
        
        # Parse JSON
        try:
            script_json = json.loads(script_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response: {script_text[:500]}...")
            raise Exception("Failed to parse JSON from Groq response")
        
        # Validate structure
        validate_script_structure(script_json)
        
        logger.info(f"✅ Script generated: {len(script_json.get('dialogue', []))} dialogue turns")
        return script_json
        
    except Exception as e:
        logger.error(f"❌ Groq script generation failed: {e}")
        raise Exception(f"Failed to generate script with Groq: {str(e)}")


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
        if "speaker" not in turn or "text" not in turn:
            raise Exception("Invalid dialogue turn structure")
        if turn["speaker"] not in speaker_ids:
            raise Exception(f"Invalid speaker reference: {turn['speaker']}")
    
    logger.info("✅ Script structure validated")
