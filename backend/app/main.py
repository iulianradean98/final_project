from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.migrations import ensure_schema
from app.db.session import engine
from app.seed import seed_demo_data


def create_app() -> FastAPI:
    app = FastAPI(
        title="Recipe Rescue API",
        version="0.1.0",
        description="REST API for matching pantry ingredients with recipe ideas.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        ensure_schema()
        if settings.seed_demo_data:
            seed_demo_data()

    return app


app = create_app()
