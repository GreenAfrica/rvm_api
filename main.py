from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.factory import detector
from app.router import router
from app.ws import router as ws_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    detector.start()
    yield
    # Shutdown
    detector.stop()

app = FastAPI(title="RVM JSON API", version="1.0.0", lifespan=lifespan)

# include routes
app.include_router(router)
app.include_router(ws_router)
