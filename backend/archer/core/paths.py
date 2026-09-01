from pathlib import Path

# From backend/archer/core/paths.py -> backend/
BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


def _resolve_frontend_dir() -> Path:
    """
    Locate the built React application.

    Two layouts have to work, because the application runs in both:

      container   /app/frontend          (the image build copies dist here)
      local dev   <repo>/frontend/dist   (the output of `npm run build`)

    The first candidate that actually contains an index.html wins. If neither
    does - a developer who has not run the frontend build yet - the first
    candidate is returned anyway and the route handler reports the situation.
    A missing frontend build should not stop the API from starting.
    """
    candidates = [
        BASE_DIR / "frontend",
        BASE_DIR.parent / "frontend" / "dist",
    ]
    for candidate in candidates:
        if (candidate / "index.html").is_file():
            return candidate
    return candidates[0]


FRONTEND_DIR = _resolve_frontend_dir()
FRONTEND_INDEX = FRONTEND_DIR / "index.html"
FRONTEND_ASSETS_DIR = FRONTEND_DIR / "assets"


def frontend_is_built() -> bool:
    """True when a built frontend is present and can be served."""
    return FRONTEND_INDEX.is_file()
