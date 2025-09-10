# coding: utf-8


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import config
from src.apis import ResourceRouter, RetrievalRouter
from src.services.db import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    db.create_db()
    yield


app = FastAPI(
    title="xButler webserver", description="Web server for ML services of xButler", version="1.1.0", lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

api_version = f"/{config.API_VERSION}"
app.include_router(ResourceRouter, prefix=api_version)
app.include_router(RetrievalRouter, prefix=api_version)
