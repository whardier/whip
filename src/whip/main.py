from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI(title="WHIP - Web Host Input Protocol")

# Determine static directory path (relative to project root)
# When running via uvicorn, cwd is typically the project root
STATIC_DIR = Path("static").resolve()

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Redirect root to static interface"""
    return RedirectResponse(url="/static/index.html")


@app.on_event("startup")
async def startup_event():
    print("WHIP server running at http://0.0.0.0:9447")
