from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
import models

app = FastAPI(
    title="Banking Audit AI System",
    description="Hệ thống Kiểm toán Ngân hàng với AI",
    version="2.0.0"
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from routers import auth, dashboard, branches, customers, misuse, cases
from routers import ai as ai_router

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(branches.router, prefix="/api/branches", tags=["Branches"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(misuse.router, prefix="/api/misuse", tags=["Misuse Analysis"])
app.include_router(cases.router, prefix="/api/cases", tags=["Cases"])
app.include_router(ai_router.router, prefix="/api/ai", tags=["AI Engine"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Banking Audit AI System", "version": "2.0.0"}


@app.on_event("startup")
def startup_event():
    # Create all tables
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        count = db.query(models.Branch).count()
        if count == 0:
            print("Database empty, seeding data...")
            from seed_data import seed_database
            seed_database(db)
            print("Seeding complete!")
        else:
            print(f"Database already has {count} branches, skipping seed.")

        # Initialize AI pipeline (load from disk or train from scratch)
        print("Initializing AI Pipeline...")
        from ai_engine.pipeline import get_pipeline
        pipeline = get_pipeline()
        if not pipeline.classifier.is_fitted:
            print("Training ML models for first time (this may take ~30 seconds)...")
            pipeline.train(db)
            pipeline.score_all(db)
            print("AI Pipeline ready!")
        else:
            print(f"AI models loaded from disk. Last trained: {pipeline.last_trained}")

    except Exception as e:
        print(f"Error during startup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
