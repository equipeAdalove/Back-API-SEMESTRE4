from fastapi import FastAPI
<<<<<<< HEAD
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

react_build_dir = os.path.join(os.path.dirname(__file__), "dist")

# Serve todo o build do React
app.mount("/", StaticFiles(directory=react_build_dir, html=True), name="react")
=======
from fastapi.middleware.cors import CORSMiddleware
from routes import pdf_routes


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdf_routes.router, prefix="/api")

>>>>>>> 6de6b5d (:tada: Commit inicial - backend FastAPI para extração de dados de PDF com Ollama (Qwen3) e geração de Excel)
