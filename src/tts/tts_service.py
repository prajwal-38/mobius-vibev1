import asyncio
import edge_tts
import os
# Remove playsound import
# from playsound import playsound
import logging

# Imports for streaming playback
import io

try:
    # print("Attempting to import sounddevice...")
    import sounddevice as sd
    # print("Successfully imported sounddevice.")
except Exception as e:
    # print(f"ERROR importing sounddevice: {e}")
    sd = None # Indicate failure

try:
    # print("Attempting to import soundfile...")
    import soundfile as sf
    # print("Successfully imported soundfile.")
except Exception as e:
    # print(f"ERROR importing soundfile: {e}")
    sf = None # Indicate failure

try:
    # print("Attempting to import numpy...")
    import numpy as np
    # print("Successfully imported numpy.")
except Exception as e:
    # print(f"ERROR importing numpy: {e}")
    np = None # Indicate failure

# Setup logger for TTS service
logger = logging.getLogger(__name__)

# Remove OUTPUT_FILE definition as we stream directly
# OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output.mp3")

# Define voice (example: Microsoft David - English US)
# You can list available voices using: edge-tts --list-voices
VOICE = "en-US-BrianNeural"
async def speak_text_async(text: str):
    # print("--- speak_text_async() started ---") # DEBUG PRINT
    """Asynchronously generates speech from text using edge-tts and streams playback."""
    if not text:
        logger.warning("speak_text_async called with empty text.")
        return

    logger.info(f"Streaming speech for: '{text[:50]}...' using voice {VOICE}")
    communicate = edge_tts.Communicate(text, VOICE)
    try:
        # --- Streaming Playback Logic ---
        # Define audio parameters (adjust if necessary, check edge-tts documentation for specifics)
        samplerate = 24000  # Common for edge-tts
        channels = 1
        dtype = 'float32' # Data type for sounddevice

        # --- Playback Logic (Accumulate then Play) ---
        audio_buffer = io.BytesIO()
        logger.info("Accumulating audio chunks...")
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # Optional: log word boundaries
                # logger.debug(f"Word boundary: Offset={chunk['offset']}, Text='{chunk['text']}'")
                pass

        audio_buffer.seek(0) # Rewind buffer to the beginning
        logger.info("Finished accumulating audio. Decoding and playing...")

        if audio_buffer.getbuffer().nbytes == 0:
            logger.warning("No audio data received from TTS stream.")
            return

        try:
            # Decode the entire accumulated MP3 data
            audio_data, read_samplerate = sf.read(audio_buffer, dtype='float32')

            if audio_data.size > 0:
                logger.info(f"Decoded audio data (Shape: {audio_data.shape}, Sample Rate: {read_samplerate}). Playing...")
                # Play the decoded audio using sounddevice
                # Note: sd.play is blocking by default in this context (called via asyncio.run)
                # If called from an already running loop, consider running sd.play in an executor.
                sd.play(audio_data, read_samplerate)
                sd.wait() # Wait for playback to finish
                logger.info("Finished playing audio.")
            else:
                logger.warning("Decoded audio data is empty.")

        except Exception as decode_play_e:
            logger.error(f"Error decoding or playing accumulated audio: {decode_play_e}", exc_info=True)

        # --- End Playback Logic ---

    except Exception as e: # Catch generic exceptions during stream accumulation
        logger.error(f"Error during TTS stream processing: {e}", exc_info=True)
    # Removed redundant general exception catch here, handled by the one above and the decode/play try-except

def speak_text(text: str):
    # print("--- speak_text() started ---") # DEBUG PRINT
    """Synchronous wrapper for the async TTS function."""
    try:
        asyncio.run(speak_text_async(text))
    except RuntimeError as e:
        # Handle cases where asyncio event loop is already running (e.g., in Jupyter)
        if "cannot run nested event loops" in str(e):
            logger.warning("Asyncio loop already running. Using existing loop for TTS.")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(speak_text_async(text))
        else:
            logger.error(f"RuntimeError running TTS: {e}", exc_info=True)
            raise
    except Exception as e:
        logger.error(f"Unexpected error running TTS: {e}", exc_info=True)
        raise

# Example usage (for testing)
if __name__ == '__main__':
    # print("--- tts_service.py __main__ started ---") # DEBUG PRINT
    logging.basicConfig(level=logging.INFO)
    test_text = "Hello! This is a test of the Edge Text-to-Speech service."
    # print(f"Testing TTS with text: '{test_text}'")
    # print("--- Calling speak_text() from __main__ ---") # DEBUG PRINT
    speak_text(test_text)    # print("--- speak_text() finished in __main__ ---") # DEBUG PRINT
    # print("TTS test complete.")
