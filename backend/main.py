import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from backend.database import engine, Base
from backend.routes import users, preferences

# Create all tables on startup (idempotent — safe to call every time)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CrunchTime API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(preferences.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/vapid-public-key")
def vapid_public_key():
    """The browser needs this key to create a push subscription."""
    return {"publicKey": os.getenv("VAPID_PUBLIC_KEY", "")}


@app.get("/sw.js")
def service_worker():
    """Serve the service worker from the root path (required for full-scope push events)."""
    return FileResponse("frontend/sw.js", media_type="application/javascript")


@app.get("/")
def index():
    return FileResponse("frontend/subscribe.html")
