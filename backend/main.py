from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import auth, portfolio, analytics

app = FastAPI(
    title="BidUp Portfolio Intelligence API",
    description="Educational & Analytical Portfolio Intelligence API (Modules 1–14)",
    version="1.0.0"
)

# CORS Middleware to allow Reflex frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount core routers
app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {
        "app": "BidUp Portfolio Intelligence",
        "version": "1.0.0",
        "status": "operational",
        "compliance": "Descriptive & educational analytical platform only. No personalized buy/sell advice."
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
