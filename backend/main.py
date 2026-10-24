from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.api.v1.exceptions import register_exception_handlers
from backend.src.api.v1.applications import router as applications_router
from backend.src.api.v1.assistant import router as assistant_router
from backend.src.api.v1.bank import router as bank_router
from backend.src.api.v1.catalog import router as catalog_router
from backend.src.api.v1.mocks import router as mocks_router
from backend.src.api.v1.notifications import router as notifications_router
from backend.src.api.v1.profile import router as profile_router
from backend.src.api.v1.recommendations import router as recommendations_router
from backend.src.api.v1.system import router as system_router
from backend.src.database import SessionLocal, engine
from backend.src.models import Base, Company, SCORING_POLICY_VERSION, ScoringRule
from backend.src.schemas.errors import ErrorResponse
from backend.src.scoring.rules import MODEL_VERSION
from backend.src.seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.get(ScoringRule, SCORING_POLICY_VERSION) is None:
            db.add(
                ScoringRule(
                    version=SCORING_POLICY_VERSION,
                    parameters={"modelVersion": MODEL_VERSION},
                )
            )
            db.commit()
        if db.query(Company.id).first() is None:
            seed_demo_data(db)
    yield

app = FastAPI(
    lifespan=lifespan,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Role is not allowed"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
        409: {"model": ErrorResponse, "description": "State conflict"},
        422: {"model": ErrorResponse, "description": "Request validation failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(applications_router, prefix="/api/v1", tags=["applications"])
app.include_router(assistant_router, prefix="/api/v1", tags=["assistant"])
app.include_router(bank_router, prefix="/api/v1", tags=["bank"])
app.include_router(catalog_router, prefix="/api/v1", tags=["catalog"])
app.include_router(mocks_router, prefix="/api/v1", tags=["mocks"])
app.include_router(notifications_router, prefix="/api/v1", tags=["notifications"])
app.include_router(profile_router, prefix="/api/v1", tags=["profile"])
app.include_router(recommendations_router, prefix="/api/v1", tags=["recommendations"])
app.include_router(system_router, prefix="/api/v1", tags=["system"])
