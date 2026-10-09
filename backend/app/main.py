"""Main FastAPI application entrypoint and lifespan management."""

from contextlib import asynccontextmanager
import json
import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models.entities import DatasetRecord, ModelTrainingRecord, TicketRecord, EvaluationRecord
from app.services.dataset_service import dataset_service
from app.services.ml_engine import ml_engine
from app.api.auth import router as auth_router
from app.api.datasets_api import router as datasets_router
from app.api.models_api import router as models_router
from app.api.tickets_api import router as tickets_router
from app.api.review_api import router as review_router
from app.api.system_api import router as system_router

logger = logging.getLogger("support_intent_observatory")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.check_production_guard()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        dataset = dataset_service.seed_default_dataset_if_empty(db)
        active_model = db.query(ModelTrainingRecord).filter(ModelTrainingRecord.is_active == True).first()

        if active_model and active_model.model_file_path:
            ml_engine.load_model(active_model.id, active_model.model_file_path)
        elif dataset:
            tickets = db.query(TicketRecord).filter(TicketRecord.dataset_id == dataset.id).all()
            if len(tickets) >= 10:
                hparams = {"ngram_min": 1, "ngram_max": 2, "min_df": 1, "max_df": 0.95, "c_regularization": 1.0, "max_iter": 500, "test_size": 0.25}
                model_rec = ModelTrainingRecord(name="baseline_support_intent_model", dataset_id=dataset.id, status="training", hyperparameters=json.dumps(hparams), is_active=True)
                db.add(model_rec)
                db.flush()

                t0 = time.time()
                eval_res = ml_engine.train_and_evaluate([t.text for t in tickets], [t.actual_intent for t in tickets], hparams, model_rec.id)
                overall = eval_res["overall_metrics"]

                model_rec.status = "ready"
                model_rec.train_sample_count = eval_res["train_sample_count"]
                model_rec.test_sample_count = eval_res["test_sample_count"]
                model_rec.accuracy = overall["accuracy"]
                model_rec.macro_f1 = overall["macro_f1"]
                model_rec.weighted_f1 = overall["weighted_f1"]
                model_rec.training_latency_ms = round((time.time() - t0) * 1000, 2)
                model_rec.model_file_path = eval_res["model_file_path"]

                db.add(EvaluationRecord(
                    model_id=model_rec.id,
                    overall_metrics=json.dumps(overall),
                    per_class_metrics=json.dumps(eval_res["per_class_metrics"]),
                    confusion_matrix=json.dumps(eval_res["confusion_matrix"]),
                    discriminative_features=json.dumps(eval_res["discriminative_features"]),
                    baseline_comparison=json.dumps(eval_res["baseline_comparison"]),
                ))
                db.commit()
    except Exception as exc:
        logger.warning("Startup seeding notice: %s", exc)
        db.rollback()
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Support Intent Observatory: TF-IDF Intent Classification and Triage Routing.",
        lifespan=lifespan,
    )
    application.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled error: %s", exc)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "InternalServerError", "message": "Unexpected error", "path": str(request.url.path)})

    application.include_router(auth_router)
    application.include_router(datasets_router)
    application.include_router(models_router)
    application.include_router(tickets_router)
    application.include_router(review_router)
    application.include_router(system_router)
    return application


app = create_app()
