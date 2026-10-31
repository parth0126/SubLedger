from fastapi import FastAPI

from app.core.config import get_settings
from app.core.error_handlers import register_exception_handlers
from app.routes import routers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="SaaS subscription and billing management API.",
        debug=settings.debug,
    )
    register_exception_handlers(app)
    for router in routers:
        app.include_router(router)

    @app.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
