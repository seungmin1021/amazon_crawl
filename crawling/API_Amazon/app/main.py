from fastapi import FastAPI
from app.api import ranking
from app.api import product_master

app = FastAPI()

app.include_router(ranking.router, prefix="/api/stream", tags=["ranking"])
app.include_router(product_master.router, prefix="/api/stream", tags=["product"])