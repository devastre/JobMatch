from fastapi import FastAPI
from routers import auth
from database import engine, Base

app = FastAPI(
    title="JobMatch API",
    description="API for JobMatch platform",
    version="1.0.0",
    docs_url="/docs"
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {"message": "Welcome to JobMatch API"}
