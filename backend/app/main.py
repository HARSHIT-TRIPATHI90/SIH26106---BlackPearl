import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes import router
from app import neo4j_client

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Black Pearl — Email Threat Forensics Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    try:
        neo4j_client.ensure_constraints()
    except Exception as e:
        logging.warning("Neo4j not reachable at startup (%s) — start it before analyzing email.", e)


@app.on_event("shutdown")
def on_shutdown():
    neo4j_client.close_driver()


@app.get("/api/health")
def health():
    return {"status": "ok"}
