import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
NCM_CSV_PATH = os.getenv("NCM_CSV_PATH", "C:/csv/ncm.csv")
TOP_K = int(os.getenv("TOP_K", "5"))
