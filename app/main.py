from fastapi import FastAPI

from app.api.ws import router as ws_router

app = FastAPI(title="2D Platformer Server")

app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ok"}
