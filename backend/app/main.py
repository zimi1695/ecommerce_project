from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.routers import analytics
from backend.app.routers import dashboard
from backend.app.routers import products
from backend.app.routers import sessions
from backend.app.routers import users


app = FastAPI(
    title="E-commerce User Behavior Analysis System",
    version="1.0.0",
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": str(exc.detail),
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "Request validation failed",
            "data": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "data": None,
        },
    )


app.include_router(
    dashboard.router,
    prefix="/api/dashboard",
    tags=["Dashboard"],
)

app.include_router(
    products.router,
    prefix="/api/products",
    tags=["Products"],
)

app.include_router(
    users.router,
    prefix="/api/users",
    tags=["Users"],
)

app.include_router(
    analytics.router,
    prefix="/api/analytics",
    tags=["Analytics"],
)

app.include_router(
    sessions.router,
    prefix="/api/sessions",
    tags=["Sessions"],
)


@app.get("/")
def root():
    return {
        "name": "E-commerce User Behavior Analysis System",
        "status": "running",
    }