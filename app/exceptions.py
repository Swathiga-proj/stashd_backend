from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.logger import logger

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()} | Path: {request.url}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Invalid input",
            "errors": exc.errors()
        }
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)} | Path: {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Database error occurred"
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)} | Path: {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error"
        }
    )