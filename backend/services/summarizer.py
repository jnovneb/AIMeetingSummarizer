# services/summarizer.py
# Summarizer using Ollama (local) via LangChain community integration.
# Falls back to a simple heuristic summarizer if Ollama isn't available.

import os
from typing import Tuple
import json
import re

from dotenv import load_dotenv
load_dotenv()

# Environment config
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")  # LangChain's Ollama client uses default if not provided

# Try to import LangChain Ollama wrapper; if not installed or fails, we'll fallback.
try:
    from langchain_community.llms import Ollama
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_OLLAMA_AVAILABLE = True
except Exception:
    LANGCHAIN_OLLAMA_AVAILABLE = False


def _heuristic_summarize(transcript: str, language: str = "en") -> Tuple[str, str]:
    """
    Simple fallback summarizer when Ollama is not available.
    Returns (summary, tasks_text).
    """
    # basic sentence split
    sentences = re.split(r'(?<=[.!?])\s+', transcript.strip())
    summary = " ".join(sentences[:4]).strip()
    if not summary:
        summary = transcript[:500].strip()

    tasks = []
    lower = transcript.lower()
    keywords_en = ["todo", "action", "action item", "task", "follow up", "assign", "deadline"]
    keywords_es = ["pendiente", "tarea", "accion", "acción", "seguir", "asignar", "fecha límite", "plazo"]

    keywords = keywords_es if language == "es" else keywords_en

    for line in transcript.splitlines():
        for kw in keywords:
            if kw in line.lower():
                tasks.append(line.strip())
                break

    if not tasks:
        # pick some likely action sentences
        for s in sentences:
            s_low = s.lower()
            if language == "es":
                if any(w in s_low for w in ["hará", "haremos", "necesitamos", "asignar", "debería", "plazo"]):
                    tasks.append(s.strip())
            else:
                if any(w in s_low for w in ["will", "we will", "need to", "assign", "deadline", "please"]):
                    tasks.append(s.strip())
            if len(tasks) >= 6:
                break

    tasks_text = "\n".join(tasks) if tasks else "No explicit tasks detected."

    return summary, tasks_text


def _build_prompt(transcript: str, language: str = "en") -> str:
    """
    Build a language-aware prompt for the LLM.
    We ask for a short summary and a JSON array of tasks to make parsing deterministic.
    """
    if language == "es":
        prompt = f"""
You are an assistant that summarizes meeting transcripts in Spanish.
Given the transcript below, produce a JSON object with fields:
- summary: a concise Spanish summary (3-6 sentences).
- tasks: an array of task strings (short), include assignee/deadline if present.

Transcript:
{transcript}

Return ONLY valid JSON, nothing else.
"""
    else:
        prompt = f"""
You are an assistant that summarizes meeting transcripts in English.
Given the transcript below, produce a JSON object with fields:
- summary: a concise English summary (3-6 sentences).
- tasks: an array of task strings (short), include assignee/deadline if present.

Transcript:
{transcript}

Return ONLY valid JSON, nothing else.
"""
    return prompt.strip()


def _parse_json_response(text: str) -> Tuple[str, str]:
    """
    Try to parse JSON from model response. Returns (summary, tasks_text).
    If parsing fails, fallback to naive extraction.
    """
    try:
        payload = json.loads(text)
        summary = payload.get("summary", "")
        tasks_list = payload.get("tasks", [])
        if isinstance(tasks_list, list):
            tasks_text = "\n".join(tasks_list)
        else:
            tasks_text = str(tasks_list)
        return summary.strip(), tasks_text.strip()
    except Exception:
        # fallback: try to extract by regex
        # try to locate "summary" and "tasks" substrings
        lower = text.lower()
        # naive fallback: first 3 sentences as summary, lines with '-' or bullets as tasks
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        summary = " ".join(sentences[:3]).strip()
        tasks_lines = []
        for line in text.splitlines():
            if line.strip().startswith(("-", "*")) or "-" in line:
                tasks_lines.append(line.strip().lstrip("-* ").strip())
        tasks_text = "\n".join(tasks_lines) if tasks_lines else "No explicit tasks detected."
        return summary, tasks_text


def summarize_with_ollama(transcript: str, language: str = "en") -> Tuple[str, str]:
    """
    Summarize with Ollama via LangChain. Returns (summary, tasks_text).
    If Ollama/LangChain is unavailable or fails, falls back to heuristic summarizer.
    """
    if not LANGCHAIN_OLLAMA_AVAILABLE:
        return _heuristic_summarize(transcript, language=language)

    try:
        # Initialize Ollama LLM (LangChain wrapper will use local Ollama server)
        llm = Ollama(model=OLLAMA_MODEL)  # uses default endpoint for local Ollama server

        prompt_text = _build_prompt(transcript, language=language)
        prompt = PromptTemplate(input_variables=["content"], template="{content}")

        chain = LLMChain(llm=llm, prompt=prompt)
        # Run chain with the prompt_text as the only variable
        raw = chain.run(content=prompt_text)

        # Try to parse JSON from raw response
        summary, tasks_text = _parse_json_response(raw)
        return summary, tasks_text
    except Exception:
        # On any failure, revert to heuristic
        return _heuristic_summarize(transcript, language=language)


def generate_summary_and_tasks(transcript: str, language: str = "en") -> Tuple[str, str]:
    """
    Public function used by app.py to obtain (summary, tasks).
    """
    return summarize_with_ollama(transcript, language=language)
