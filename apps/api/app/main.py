from fastapi import FastAPI

from app.errors import install_error_handlers
from app.routers import auth, documents, folders

app = FastAPI(title="Verso API", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
install_error_handlers(app)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(folders.router)
app.include_router(documents.router)
