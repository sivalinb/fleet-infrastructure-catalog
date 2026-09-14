import os
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .catalog import Batch, backstage_export, impact, ingest, snapshot
from .fixtures import scenario, seed
from .models import Audit, make_database

ROOT = Path(__file__).resolve().parents[2]


def create_app(database_url=None):
    engine, factory = make_database(database_url)
    with factory.begin() as db:
        seed(db)

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()

    app = FastAPI(
        title="Fleet Infrastructure Catalog API", version="1.0.0", lifespan=lifespan
    )
    app.state.factory = factory
    catalog_lock = (
        threading.Lock()
    )  # One API worker; serialize full projection rebuilds.

    @app.middleware("http")
    async def protect(request, call_next):
        token = os.getenv("CATALOG_API_TOKEN", "")
        if (
            request.url.path.startswith("/api/")
            and token
            and not secrets.compare_digest(
                request.headers.get("authorization", ""), "Bearer " + token
            )
        ):
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=401, content={"detail": "Invalid API token"}
            )
        try:
            length = int(request.headers.get("content-length", "0") or "0")
        except ValueError:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=400, content={"detail": "Invalid content length"}
            )
        if length > 4 * 1024 * 1024:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=413, content={"detail": "Import exceeds 4 MB"}
            )
        if request.method == "POST" and len(await request.body()) > 4 * 1024 * 1024:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=413, content={"detail": "Import exceeds 4 MB"}
            )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/health")
    def health():
        return {"status": "ready", "database": engine.dialect.name, "version": "1.0.0"}

    @app.get("/api/catalog")
    def catalog():
        with factory() as db:
            return snapshot(db)

    @app.get("/api/impact/{entity_id:path}")
    def affected(entity_id):
        with factory() as db:
            try:
                return impact(snapshot(db), entity_id)
            except KeyError as e:
                raise HTTPException(404, str(e))

    @app.post("/api/sources/{source_id}/sync")
    def sync(source_id, batch: Batch):
        try:
            with catalog_lock, factory.begin() as db:
                return ingest(db, source_id, batch)
        except KeyError as e:
            raise HTTPException(404, str(e))
        except (ValueError, IntegrityError) as e:
            raise HTTPException(409, str(e)[:200])

    @app.post("/api/catalog/scenarios/{name}")
    def inject(name):
        try:
            with catalog_lock, factory.begin() as db:
                scenario(db, name)
                return snapshot(db)
        except KeyError as e:
            raise HTTPException(404, str(e))

    @app.get("/api/catalog/export/backstage")
    def export():
        with factory() as db:
            return Response(
                backstage_export(snapshot(db)),
                media_type="application/yaml",
                headers={
                    "Content-Disposition": "attachment; filename=catalog-info.yaml"
                },
            )

    @app.get("/api/audit")
    def audit():
        with factory() as db:
            return [
                {
                    "id": a.id,
                    "entity_id": a.entity_id,
                    "action": a.action,
                    "detail": a.detail,
                    "created_at": a.created_at.isoformat(),
                }
                for a in db.scalars(select(Audit).order_by(Audit.id.desc()).limit(150))
            ]

    app.mount(
        "/docs-guide", StaticFiles(directory=ROOT / "docs", html=True), name="guide"
    )
    return app


def app_factory():
    return create_app()
