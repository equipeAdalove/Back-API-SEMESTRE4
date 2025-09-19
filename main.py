from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

react_build_dir = os.path.join(os.path.dirname(__file__), "dist")

# Serve todo o build do React
app.mount("/", StaticFiles(directory=react_build_dir, html=True), name="react")
