from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from backend.api.routers import graph_api, lab_api


MAX_REQUEST_BYTES = 1025 * 1024 * 1024

app = FastAPI(
    title="Instagram Epic Graph API",
    description="Análisis local y temporal de exportaciones oficiales de Instagram.",
    version="0.1.0",
)


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            is_too_large = int(content_length) > MAX_REQUEST_BYTES
        except ValueError:
            is_too_large = True
        if is_too_large:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "El archivo supera el límite permitido de 1 GB."},
            )
    response = await call_next(request)
    if request.url.path.startswith("/api/lab/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response

app.include_router(graph_api.router, prefix="/api")
app.include_router(lab_api.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Servicio de análisis disponible."}
