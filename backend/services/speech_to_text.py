import wave
import json
from vosk import Model, KaldiRecognizer

# Paths to language models
MODEL_PATHS = {
    "es": "models/vosk-model-small-es-0.42",
    "en": "models/vosk-model-small-en-us-0.15"
}

def transcribe_audio(file_path, language="en"):
    """
    Transcribe an audio file using VOSK.
    :param file_path: Path to the audio file
    :param language: 'es' for Spanish, 'en' for English
    :return: Transcribed text
    """
    if language not in MODEL_PATHS:
        raise ValueError(f"Unsupported language: {language}")

    model_path = MODEL_PATHS[language]
    model = Model(model_path)

    wf = wave.open(file_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    text = ""
    while True:
        data = wf.readframes(4000)
        if not data:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text += res.get("text", "") + " "
    text += json.loads(rec.FinalResult()).get("text", "")
    return text.strip()
