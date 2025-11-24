from google.cloud import texttospeech
from app.core.config import settings
from app.utils.logger import logger
import io
from pydub import AudioSegment

def synthesize_speech(text: str, voice_name: str = "en-US-Neural2-D") -> bytes:
    """Synthesize speech for a single dialogue turn."""
    client = texttospeech.TextToSpeechClient.from_service_account_file(settings.gcs_credentials_path)
    synthesis_input = texttospeech.SynthesisInput(text=text)
    # Choose a neural English voice, or pick different ones for each character
    voice_params = texttospeech.VoiceSelectionParams(
        language_code="en-US", name=voice_name)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice_params, audio_config=audio_config
    )
    return response.audio_content  # bytes

def merge_dialogue_to_audio(dialogue, speakers, voice_map) -> bytes:
    segments = []
    for turn in dialogue:
        speaker_id = turn["speaker"]
        text = turn["text"]
        # Map speaker id to a GCP TTS voice
        voice_name = voice_map.get(speaker_id, "en-US-Neural2-D")
        logger.info(f"Synthesizing: [{speaker_id}] {voice_name}: {text[:30]}...")
        audio_bytes = synthesize_speech(text, voice_name)
        seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        segments.append(seg)
        # Add a 0.3s pause after each turn
        segments.append(AudioSegment.silent(duration=300))

    final_audio = sum(segments[1:], segments[0]) if segments else AudioSegment.silent(duration=1000)
    buf = io.BytesIO()
    final_audio.export(buf, format="mp3")
    return buf.getvalue()
