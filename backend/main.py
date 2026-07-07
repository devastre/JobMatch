from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, cv, search
from database import engine, Base
import models  # noqa: F401 — ensures all models are registered before create_all

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JobMatch API",
    description="API for JobMatch platform",
    version="1.0.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(cv.router, prefix="/api/cv", tags=["cv"])

@app.get("/")
def read_root():
    return {"message": "Welcome to JobMatch API"}
