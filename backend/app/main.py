
from contextlib import asynccontextmanager
from app.routes.products import router as products_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.query import router as query_router
from app.neo4j_client import close_driver
from app.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_driver()


app = FastAPI(
    title="AgentLens API",
    description="Natural-language electronics product discovery powered by Neo4j.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5180",
"http://127.0.0.1:5180",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(products_router)
app.include_router(query_router)
@app.get("/")
def root():
    return {
        "message": "Welcome to AgentLens API",
        "docs": "/docs",
        "health": "/health",
    }
