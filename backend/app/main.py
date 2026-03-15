from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import products

app = FastAPI(
    title="ModelCart API",
    description="LLM/AI Agent-optimized e-commerce API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
