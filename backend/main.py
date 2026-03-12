from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.config import engine, Base
from app.models.user import User
from app.models.entity import Entity
from app.models.entity_ownership import EntityOwnership
from app.models.document import Document
from app.metrics.models import FinancialMetrics
from app.credit_scoring.models import CreditScore, CreditScoringHistory, UnderwritingDecision
from app.cam.models import CAMReport
from app.auth.routes import router as auth_router
from app.entities.routes import router as entity_router
from app.documents.routes import router as documents_router
from app.documents.preview import router as preview_router
from app.ai_pipeline.routes import router as ai_pipeline_router
from app.metrics.routes import router as metrics_router
from app.credit_scoring.routes import router as credit_scoring_router
from app.explainability.routes import router as explainability_router
from app.cam.routes import router as cam_router
from app.extraction.models import ExtractionResult
from app.extraction.routes import router as extraction_router
from app.research_engine.routes import router as research_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Credit Underwriting API",
    description="AI-powered Enterprise Credit Underwriting System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(entity_router)
app.include_router(documents_router)
app.include_router(preview_router)
app.include_router(ai_pipeline_router)
app.include_router(metrics_router)
app.include_router(credit_scoring_router)
app.include_router(explainability_router)
app.include_router(cam_router)
app.include_router(extraction_router)
app.include_router(research_router)

@app.get("/")
def read_root():
    return {"message": "Credit Underwriting API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
