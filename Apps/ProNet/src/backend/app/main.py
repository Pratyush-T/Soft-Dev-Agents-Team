"""ProNet Backend Application Entrypoint.

Configures FastAPI ASGI gateway, database lifespan hooks, CORS middleware,
structured JSON request logging, static uploads serving, domain routers,
and uniform RFC-compliant error handlers.
"""
import os
import time
import uuid
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_v1_router
from app.api.ws import ws_router
from app.core.config import settings
from app.core.database import async_session_factory, engine, init_db
from app.core.exceptions import ProNetException
from app.core.logging import logger
from app.services.seeder import seed_database


def resolve_upload_directory() -> str:
    """Resolve and ensure uploads directory path exists across environments."""
    configured_dir = os.path.abspath(settings.PRONET_UPLOAD_DIR)
    if os.path.isdir(configured_dir):
        target = configured_dir
    else:
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(backend_root, "uploads")
        if os.path.isdir(candidate):
            target = candidate
        else:
            target = configured_dir

    os.makedirs(os.path.join(target, "avatars"), exist_ok=True)
    os.makedirs(os.path.join(target, "posts"), exist_ok=True)
    os.makedirs(os.path.join(target, "resumes"), exist_ok=True)
    return target


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager handling startup initialization and shutdown disposal."""
    logger.info("Initializing ProNet SQLite schema with WAL mode...")
    await init_db()

    logger.info("Running deterministic database seeder...")
    async with async_session_factory() as session:
        seeded = await seed_database(session, force=False)
        if seeded:
            logger.info("Deterministic database seeding completed successfully.")
        else:
            logger.info("Database already contains data; seeding bypassed.")

    logger.info("ProNet backend ready to accept connections.")
    yield

    logger.info("Disposing database connection pool...")
    await engine.dispose()
    logger.info("ProNet backend shutdown complete.")


app = FastAPI(
    title="ProNet Professional Network API",
    description="High-performance, local-first professional networking platform with real-time WebSockets.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# 1. CORS MIDDLEWARE
# ------------------------------------------------------------------------------
allowed_origins = [
    settings.PRONET_CLIENT_ORIGIN,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
unique_origins = list({o for o in allowed_origins if o})

app.add_middleware(
    CORSMiddleware,
    allow_origins=unique_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# ------------------------------------------------------------------------------
# 2. REQUEST ID & STRUCTURED LOGGING MIDDLEWARE
# ------------------------------------------------------------------------------
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Assign X-Request-ID header, measure duration, and emit structured JSON log."""
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:16]}"
    request.state.request_id = request_id
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            f"Unhandled exception during {request.method} {request.url.path} after {duration_ms}ms: {exc}",
            exc_info=True,
            extra={"request_id": request_id},
        )
        raise exc

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    client_ip = request.client.host if request.client else "127.0.0.1"
    logger.info(
        f"{request.method} {request.url.path} {response.status_code} - {duration_ms}ms",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
        },
    )
    return response


# ------------------------------------------------------------------------------
# 3. GLOBAL EXCEPTION HANDLERS
# ------------------------------------------------------------------------------
@app.exception_handler(ProNetException)
async def pronet_exception_handler(request: Request, exc: ProNetException) -> JSONResponse:
    """Format domain-specific ProNet exceptions into standard error envelope."""
    request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:16]}")
    payload = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "status_code": exc.status_code,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": request.url.path,
            "request_id": request_id,
            "details": exc.details,
        }
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Format Pydantic schema validation failures into uniform error envelope."""
    request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:16]}")
    errors = exc.errors()

    code = "VALIDATION_ERROR"
    message = "Request validation failed. Please check submitted fields."

    # Intercept specific known business rules triggered in Pydantic validators
    for err in errors:
        msg = str(err.get("msg", ""))
        if "END_DATE_BEFORE_START_DATE" in msg:
            code = "END_DATE_BEFORE_START_DATE"
            message = "End date cannot precede the start date."
            break
        elif "SALARY_MAX_MUST_EXCEED_MIN" in msg:
            code = "SALARY_MAX_MUST_EXCEED_MIN"
            message = "Maximum salary must be greater than or equal to minimum salary."
            break

    details: Dict[str, Any] = {
        "errors": [
            {
                "loc": [str(loc_item) for loc_item in e.get("loc", [])],
                "msg": e.get("msg", ""),
                "type": e.get("type", ""),
            }
            for e in errors
        ]
    }

    payload = {
        "error": {
            "code": code,
            "message": message,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": request.url.path,
            "request_id": request_id,
            "details": details,
        }
    }
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload,
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Format standard Starlette HTTP exceptions into uniform error envelope."""
    request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:16]}")
    code_map = {
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "RESOURCE_NOT_FOUND",
        status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "PAYLOAD_TOO_LARGE",
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "UNSUPPORTED_MEDIA_TYPE",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMIT_EXCEEDED",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    payload = {
        "error": {
            "code": code,
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": request.url.path,
            "request_id": request_id,
            "details": {},
        }
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all unhandled exception handler generating HTTP 500 error envelope."""
    request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:16]}")
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
        extra={"request_id": request_id},
    )
    payload = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred. Please try again later.",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": request.url.path,
            "request_id": request_id,
            "details": {"error_type": type(exc).__name__},
        }
    }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload,
        headers={"X-Request-ID": request_id},
    )


# ------------------------------------------------------------------------------
# 4. STATIC FILE MOUNTS
# ------------------------------------------------------------------------------
upload_directory = resolve_upload_directory()
app.mount("/uploads", StaticFiles(directory=upload_directory), name="uploads")


# ------------------------------------------------------------------------------
# 5. ROUTER INCLUSION
# ------------------------------------------------------------------------------
app.include_router(api_v1_router)
app.include_router(ws_router)


# ------------------------------------------------------------------------------
# 6. SYSTEM HEALTH & DIAGNOSTIC ENDPOINTS
# ------------------------------------------------------------------------------
@app.get("/health", tags=["System Health"])
@app.get("/api/v1/health", tags=["System Health"])
async def health_check():
    """Verify backend availability, version, and server timestamp."""
    return {
        "status": "healthy",
        "service": "pronet-backend",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
