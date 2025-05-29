from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.models.responses import HealthResponse
from src.api.routes.conversation import router as conversation_router
from src.api.routes.documentation import router as documentation_router
from src.api.routes.diagram import router as diagram_router
from src.api.routes.code import router as code_router
from src.utils.logger import configure_logging

configure_logging(
    log_level=settings.log_level,
    log_to_file=settings.log_to_file,
    max_file_size_mb=settings.max_log_file_size_mb,
    backup_count=settings.log_backup_count
)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversation_router)
app.include_router(documentation_router)
app.include_router(diagram_router)
app.include_router(code_router)

@app.get("/", response_model=HealthResponse)
def read_root():
    return HealthResponse(
        status="ok", 
        message="API running correctly with LangChain integration",
        version=settings.version
    )

@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy", 
        message="Service is running properly",
        version=settings.version
    )