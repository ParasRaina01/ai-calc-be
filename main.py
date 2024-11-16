from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import os
from apps.calculator.route import router as calculator_router
from constants import SERVER_URL, PORT, ENV

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["15 per day"]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please try again tomorrow.",
            "retry_after": str(exc.retry_after)
        }
    )
app = FastAPI(lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
@limiter.limit("15 per day")
async def root(request: Request):
    return {
        "message": "Server is running",
        "remaining_requests": request.state.view_rate_limit.remaining
    }
@calculator_router.get("/")
@limiter.limit("15 per day")
async def calculator_root(request: Request):
    return {
        "message": "Calculator endpoint",
        "remaining_requests": request.state.view_rate_limit.remaining
    }

app.include_router(calculator_router, prefix="/calculate", tags=["calculate"])

if __name__ == "__main__":
    load_dotenv()
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=SERVER_URL, port=port, reload=True)