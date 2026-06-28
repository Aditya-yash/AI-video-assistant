import whisper
import os
import requests
from pydub import AudioSegment

WHISHPER_MODEL = os.getenv("WHISHPER_MODEL","small")

_model = None

def load_model():
    global _model
    if _model is None:
        print(f"Loading Whisper model: {WHISHPER_MODEL}...")
        _model = whisper.load_model(WHISHPER_MODEL)
        print("Whisper model loaded.")
    return _model

def transcribe_chunk_whisper(chunk_path:str)->str:
    model = load_model()
    result = model.transcribe(chunk_path,task="transcribe")
    return result['text']


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route one chunk to Whisper or Sarvam depending on language choice.
    - english  → Whisper (local model)
    - hinglish → Sarvam (translates to English while transcribing)
    """
    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:

    full_transcript = "" 

    engine ="Whisper"
    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):  

        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")

        text = transcribe_chunk(chunk, language=language)  

        full_transcript += text + " "  

    print("Transcription complete.")

    return full_transcript.strip() 