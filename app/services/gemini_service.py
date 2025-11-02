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
    """
    Build the system prompt for script generation.
    
    Args:
        pdf_text: Extracted PDF text
        user_prompt: User's focus instructions
        style: Conversation style
        duration: Duration preference
        
    Returns:
        Formatted prompt string
    """
    style_enum = StyleType(style)
    style_instructions = style_enum.get_system_prompt_modifier()
    
    duration_enum = DurationType(duration)
    estimated_time = duration_enum.get_estimated_minutes()
    
    prompt = f"""You are an expert podcast script writer. Your task is to create an engaging, natural-sounding dialogue between two speakers based on the provided document.

**DOCUMENT CONTENT:**
{pdf_text[:15000]}

**USER INSTRUCTIONS:**
{user_prompt}

**CONVERSATION STYLE:**
{style_instructions}

**TARGET DURATION:**
Approximately {estimated_time} of audio content.

**OUTPUT FORMAT:**
Generate a JSON object with the following structure:
{{
  "title": "Engaging podcast episode title",
  "speakers": [
    {{"id": "speaker1", "name": "Host Name", "role": "Brief role description"}},
    {{"id": "speaker2", "name": "Guest Name", "role": "Brief role description"}}
  ],
  "dialogue": [
    {{"speaker": "speaker1", "text": "Opening statement or question..."}},
    {{"speaker": "speaker2", "text": "Response with detailed explanation..."}},
    {{"speaker": "speaker1", "text": "Follow-up question or comment..."}}
  ]
}}

**REQUIREMENTS:**
1. Create natural, conversational dialogue with realistic pauses and transitions
2. Include questions, reactions, and elaborations to maintain engagement
3. Focus on the content specified in the user instructions
4. Use appropriate technical depth for the conversation style
5. Include occasional informal language and verbal cues
6. Ensure speakers have distinct personalities and speaking patterns
7. The dialogue should be comprehensive enough to reach the target duration when spoken
8. Each speaker turn should be 1-4 sentences for natural pacing

Generate the podcast script now:"""
    
    return prompt


async def generate_script_from_pdf(
    pdf_bytes: bytes,
    user_prompt: str,
    style: str,
    duration: str
) -> Dict:
    """
    Generate podcast script from PDF using Gemini LLM.
    """
    try:
        logger.info("🤖 Generating script with Gemini LLM...")
        
        # Step 1: Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_bytes)
        
        if not pdf_text or len(pdf_text.strip()) < 100:
            raise Exception("PDF contains insufficient text content")
        
        # Step 2: Build prompt
        prompt = build_script_generation_prompt(pdf_text, user_prompt, style, duration)
        
        # Step 3: Configure Gemini model with UPDATED model name
        duration_enum = DurationType(duration)
        max_tokens = settings.get_duration_tokens(duration)
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",  # ✅ UPDATED to current model
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": max_tokens,
            }
        )
        
        logger.info(f"📝 Calling Gemini API with model: gemini-2.5-flash (max_tokens={max_tokens})...")
        
        # Step 4: Generate content
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            raise Exception("Gemini API returned empty response")
        
        logger.info(f"✅ Received response: {len(response.text)} characters")
        
        # Step 5: Parse JSON response
        script_json = parse_script_json(response.text)
        
        # Step 6: Validate script structure
        validate_script_structure(script_json)
        
        logger.info(f"✅ Script generated: {len(script_json['dialogue'])} dialogue turns")
        return script_json
        
    except Exception as e:
        logger.error(f"❌ Script generation failed: {e}")
        raise Exception(f"Failed to generate script: {str(e)}")



def parse_script_json(response_text: str) -> Dict:
    """
    Parse JSON from Gemini response, handling markdown code blocks.
    
    Args:
        response_text: Raw response from Gemini
        
    Returns:
        Parsed JSON dictionary
    """
    try:
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        # Handle `````` format
        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_code_block = False
            
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or not any(I.strip().startswith("````") for I in lines):
                    json_lines.append(line)
            
            text = "\n".join(json_lines)
        
        # Parse JSON
        script_data = json.loads(text)
        return script_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Response text: {response_text[:500]}...")
        raise Exception("Failed to parse script JSON from Gemini response")
    


def validate_script_structure(script: Dict) -> None:
    """
    Validate that the script has the required structure.
    
    Args:
        script: Parsed script dictionary
        
    Raises:
        Exception: If validation fails
    """
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
    """
    Format the script dialogue into text for TTS.
    
    Args:
        script_data: Script dictionary with speakers and dialogue
        
    Returns:
        Formatted text with speaker tags
    """
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
        
        # Step 1: Get speaker configurations
        speakers = script_data["speakers"]
        if len(speakers) < 2:
            raise Exception("Script must have at least 2 speakers")
        
        # Step 2: Map speakers to voice profiles
        voice_mapping = {
            speakers["id"]: settings.speaker_1_voice,
            speakers["id"]: settings.speaker_2_voice
        }
        
        logger.info(f"🗣️ Voice mapping: {voice_mapping}")
        
        # Step 3: Build dialogue parts
        dialogue_parts = []
        for turn in script_data["dialogue"]:
            speaker_id = turn["speaker"]
            voice_name = voice_mapping.get(speaker_id, settings.speaker_1_voice)
            text = turn["text"]
            
            dialogue_parts.append({
                "voice": voice_name,
                "text": text
            })
        
        # Step 4: Generate audio segments
        audio_segments = []
        
        for i, part in enumerate(dialogue_parts):
            logger.info(f"Generating segment {i+1}/{len(dialogue_parts)}: {part['voice']}")
            
            audio_bytes = await generate_single_audio_segment(
                text=part["text"],
                voice=part["voice"]
            )
            
            audio_segments.append(audio_bytes)
        
        # Step 5: Merge audio segments
        logger.info("🔗 Merging audio segments...")
        merged_audio = merge_audio_segments(audio_segments)
        
        logger.info(f"✅ Audio generated: {len(merged_audio)} bytes")
        return merged_audio
        
    except Exception as e:
        logger.error(f"❌ Audio generation failed: {e}")
        raise Exception(f"Failed to generate audio: {str(e)}")


async def generate_single_audio_segment(text: str, voice: str) -> bytes:
    """
    Generate a single audio segment using Gemini TTS.
    
    Args:
        text: Text to convert to speech
        voice: Voice name
        
    Returns:
        Audio bytes (WAV format)
    """
    try:
        # Configure Gemini model for TTS
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-nativ-audio-preview -09-2025",
            generation_config={
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": voice
                        }
                    }
                }
            }
        )
        
        # Generate audio
        response = model.generate_content(text)
        
        # Extract audio data
        if not response or not hasattr(response, 'audio'):
            raise Exception("No audio data in response")
        
        audio_data = response.audio.data
        return audio_data
        
    except Exception as e:
        logger.error(f"Single segment generation failed: {e}")
        return generate_silence(duration_ms=1000)


def merge_audio_segments(audio_segments: List[bytes]) -> bytes:
    """
    Merge multiple audio segments into a single file.
    
    Args:
        audio_segments: List of audio bytes (WAV format)
        
    Returns:
        Merged audio as bytes (MP3 format)
    """
    try:
        from pydub import AudioSegment
        import io
        
        logger.info(f"Merging {len(audio_segments)} audio segments...")
        
        segments = []
        for i, audio_bytes in enumerate(audio_segments):
            try:
                audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                segments.append(audio)
                
                pause = AudioSegment.silent(duration=300)
                segments.append(pause)
                
            except Exception as e:
                logger.warning(f"Failed to load segment {i}: {e}")
                continue
        
        if not segments:
            raise Exception("No valid audio segments to merge")
        
        merged = segments
        for segment in segments[1:]:
            merged += segment
        
        output_buffer = io.BytesIO()
        merged.export(
            output_buffer,
            format="mp3",
            bitrate="128k",
            parameters=["-q:a", "2"]
        )
        
        merged_bytes = output_buffer.getvalue()
        logger.info(f"✅ Merged audio: {len(merged_bytes)} bytes")
        
        return merged_bytes
        
    except Exception as e:
        logger.error(f"Audio merging failed: {e}")
        raise Exception(f"Failed to merge audio segments: {str(e)}")


def generate_silence(duration_ms: int = 1000) -> bytes:
    """
    Generate silent audio segment.
    
    Args:
        duration_ms: Duration in milliseconds
        
    Returns:
        Silent audio as bytes (WAV format)
    """
    try:
        from pydub import AudioSegment
        import io
        
        silence = AudioSegment.silent(duration=duration_ms)
        buffer = io.BytesIO()
        silence.export(buffer, format="wav")
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Failed to generate silence: {e}")
        return b""
