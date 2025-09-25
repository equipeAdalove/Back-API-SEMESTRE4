import re
import unidecode
import requests
from nltk.corpus import stopwords
import os

STOPWORDS_PT = set(stopwords.words("portuguese"))

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")

def limpar_texto(text: str) -> str:
    text = str(text).lower()
    text = unidecode.unidecode(text)
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = [w for w in text.split() if w not in STOPWORDS_PT]
    return " ".join(tokens).strip()

def _parse_ollama_response(resp):
    try:
        j = resp.json()
    except Exception:
        return resp.text or ""
    if isinstance(j, dict) and "response" in j:
        return j["response"]
    return resp.text or ""

def _first_line(text: str) -> str:
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[0] if lines else ""

def normalizar_com_ollama(texto: str) -> str:
    prompt = (
        "Normalize a descrição de um componente eletrônico em UMA linha.\n"
        "- Expanda abreviações (ex: CAP->capacitor).\n"
        "- Mantenha unidades (10UF, 100V, etc).\n"
        "- Retorne apenas a linha normalizada.\n\n"
        f"Input: {texto}\n\nResposta:"
    )
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "temperature": 0.0,
        "max_tokens": 150,
        "stream": False,
        "think": False
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=None)
    resp.raise_for_status()
    raw = _parse_ollama_response(resp)
    return _first_line(raw)

def choose_best_ncm(item_desc: str, top_candidates: list) -> str:
    prompt = (
        "Você recebe a descrição de um item e alguns candidatos NCM (cada NCM tem 8 dígitos).\n"
        "RETORNE APENAS o código NCM (8 dígitos) mais adequado.\n\n"
        f"Item: {item_desc}\n\n"
    )
    for c in top_candidates:
        prompt += f"NCM: {c['ncm']} | Descricao: {c['descricao_longa']}\n"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "temperature": 0.0,
        "max_tokens": 32,
        "stream": False,
        "think": False
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=None)
        resp.raise_for_status()
        raw = _parse_ollama_response(resp)
        m = re.search(r'\b(\d{8})\b', raw)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"Erro no LLM: {e}")
    return top_candidates[0]["ncm"]
