from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import pdf_routes, test_routes
from contextlib import asynccontextmanager
from models import models
from database.database import engine


@asynccontextmanager
async def lifespan(app:FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield
    
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdf_routes.router, prefix="/api")
app.include_router(test_routes.router, prefix="/api", tags=["TESTE"])

