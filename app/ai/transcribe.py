import whisper
import tempfile
import os
import requests

# Load model once at startup (use 'base' for speed in hackathon)
model = None

def load_model():
    global model
    if model is None:
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        print("Whisper model loaded!")
    return model

# def transcribe_audio_file(file_path):
#     """Transcribe a local audio file"""
#     m = load_model()
#     result = m.transcribe(file_path)
#     return result['text']

# def transcribe_from_url(audio_url):
#     """Download audio from URL and transcribe"""
#     try:
#         response = requests.get(audio_url, timeout=10)
#         with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
#             f.write(response.content)
#             tmp_path = f.name

#         transcript = transcribe_audio_file(tmp_path)
#         os.unlink(tmp_path)
#         return transcript
#     except Exception as e:
#         print(f"Transcription error: {e}")
#         return ""

def transcribe_from_base64(audio_base64):
    """Transcribe audio from base64 encoded string"""
    import base64
    try:
        audio_data = base64.b64decode(audio_base64)
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f:
            f.write(audio_data)
            tmp_path = f.name

        transcript = transcribe_audio_file(tmp_path)
        os.unlink(tmp_path)
        return transcript
    except Exception as e:
        print(f"Base64 transcription error: {e}")
        return ""
