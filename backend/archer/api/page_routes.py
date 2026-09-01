from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse

from ..auth.jwt import get_current_user
from ..core.paths import BASE_DIR, FRONTEND_INDEX, frontend_is_built

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def app_shell(request: Request, username: str = Depends(get_current_user)):
    """
    Serve the React application.

    The login wall is unchanged: get_current_user rejects an unauthenticated
    request and the application turns that into a redirect to /login, so the
    single-page app is only ever handed to a signed-in session.
    """
    if not frontend_is_built():
        # Deliberately explicit rather than a 404. The likely cause is a
        # developer who has not run the frontend build yet, and a bare 404
        # sends them looking in the wrong place.
        return HTMLResponse(
            "<h1>Frontend not built</h1>"
            "<p>Run <code>npm --prefix frontend install</code> then "
            "<code>npm --prefix frontend run build</code>, and reload.</p>",
            status_code=503,
        )
    return FileResponse(FRONTEND_INDEX, media_type="text/html")


@router.get("/landing")
@router.get("/chat")
async def legacy_page_redirect(request: Request):
    """
    Redirect the retired server-rendered pages to the application.

    /landing and /chat were Jinja templates, and /chat hosted the Watson
    Assistant widget. Both are gone. Anything still pointing at them - a
    bookmark, or the intended_url cookie set by the login flow - lands on the
    application rather than a 404.
    """
    return RedirectResponse(url="/", status_code=307)


@router.get("/favicon.ico")
async def favicon():
    """Serve the favicon to prevent 404 errors"""
    return FileResponse(str(BASE_DIR / "static" / "favicon.ico"))
