from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import supabase
from routers import tasks, battles, users, social

app = FastAPI(
    title="ProductivityGO API",
    description="Gamified Productivity Battle API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(battles.router)
app.include_router(users.router)
app.include_router(social.router)

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
