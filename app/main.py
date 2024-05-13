from fastapi import FastAPI
from app.routers.routes import router
from app.models.models import  Base
from app.database import engine
from app.utils.config import logger

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)  # Create tables

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
