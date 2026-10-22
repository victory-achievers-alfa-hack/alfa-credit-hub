from fastapi import FastAPI

from backend.src.api.v1.applications import router as applications_router
from backend.src.api.v1.assistant import router as assistant_router
from backend.src.api.v1.bank import router as bank_router
from backend.src.api.v1.catalog import router as catalog_router
from backend.src.api.v1.mocks import router as mocks_router
from backend.src.api.v1.profile import router as profile_router
from backend.src.api.v1.recommendations import router as recommendations_router
from backend.src.api.v1.system import router as system_router
from backend.src.database import Base, engine

app = FastAPI()

app.include_router(applications_router, prefix="/api/v1", tags=["applications"])
app.include_router(assistant_router, prefix="/api/v1", tags=["assistant"])
app.include_router(bank_router, prefix="/api/v1", tags=["bank"])
app.include_router(catalog_router, prefix="/api/v1", tags=["catalog"])
app.include_router(mocks_router, prefix="/api/v1", tags=["mocks"])
app.include_router(profile_router, prefix="/api/v1", tags=["profile"])
app.include_router(recommendations_router, prefix="/api/v1", tags=["recommendations"])
app.include_router(system_router, prefix="/api/v1", tags=["system"])


Base.metadata.create_all(bind=engine)