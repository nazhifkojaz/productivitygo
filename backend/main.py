from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import supabase
from routers import tasks, battles, users, social, invites, adventures
from scheduler import start_scheduler, shutdown_scheduler
import os

# -----------------------------------------------------------------------------
# CORS Configuration - REFACTOR-005: Security Fix
# -----------------------------------------------------------------------------
# Development: Allow localhost for frontend development
# Production: Use environment variable to specify allowed origins
# -----------------------------------------------------------------------------
if os.getenv("ENVIRONMENT") == "production":
    # Production: Read from ALLOWED_ORIGINS environment variable
    # Format: comma-separated list of allowed origins
    # Example: "https://yourdomain.github.io,https://yourdomain.com"
    allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
    if allowed_origins_str:
        allow_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]
    else:
        # Fallback to production domain if env var not set (should be configured)
        allow_origins = []  # Empty list will be caught by error below
else:
    # Development: Allow localhost for Vite dev server
    allow_origins = [
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Alternative dev server
        "http://127.0.0.1:3000",
    ]

# Validate CORS configuration
if not allow_origins:
    raise ValueError(
        "CORS not configured. Set ALLOWED_ORIGINS environment variable "
        "or run in development mode with ENVIRONMENT=development"
    )

app = FastAPI(
    title="ProductivityGO API",
    description="Gamified Productivity Battle API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api")
app.include_router(battles.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(social.router, prefix="/api")
app.include_router(invites.router, prefix="/api")
app.include_router(adventures.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Start background scheduler on app startup"""
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background scheduler on app shutdown"""
    shutdown_scheduler()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "ProductivityGO API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/db-health")
def db_health_check():
    try:
        # Simple query to check connection (fetching 1 profile)
        response = supabase.table("profiles").select("count", count="exact").limit(1).execute()
        return {"status": "connected", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
