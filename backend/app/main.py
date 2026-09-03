import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.session import init_tables, SessionLocal
from app.database.seed_data import reset_and_seed_database
from app.api import games, cart, library, users, assistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gamehub")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic AI Game Store powered by LangGraph, LangChain, FastAPI, and MySQL",
    version="1.0.0"
)

# CORS setup for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing GameHub database tables...")
    init_tables()
    logger.info("Seeding catalog and refreshing user session state (0 games in library)...")
    db = SessionLocal()
    try:
        reset_and_seed_database(db, reset_user_data=True)
    finally:
        db.close()
    logger.info("GameHub database initialized and refreshed successfully.")


# Mount API Routers
app.include_router(games.router, prefix=settings.API_V1_STR)
app.include_router(cart.router, prefix=settings.API_V1_STR)
app.include_router(library.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "database": settings.DB_NAME,
        "llm_provider": settings.LLM_PROVIDER,
    }
