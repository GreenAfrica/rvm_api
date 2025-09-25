from fastapi import FastAPI
from app.factory import detector
from app.router import router
from app.ws import router as ws_router

app = FastAPI(title="RVM JSON API", version="1.0.0")

# include routes
app.include_router(router)
app.include_router(ws_router)

# startup / shutdown
@app.on_event("startup")
async def startup_event():
    detector.start()

@app.on_event("shutdown")
async def shutdown_event():
    detector.stop()
