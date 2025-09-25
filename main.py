import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
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

react_build_dir = os.path.join(os.path.dirname(__file__), "dist")

app.mount("/", StaticFiles(directory=react_build_dir, html=True), name="react")