from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import logging
from app.api.routes import code, chat, websocket, test, collection_data
from app.databases.singletons import get_mongo_db


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('pymongo').setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_mongo_db()
    yield
    mdb = await get_mongo_db()
    mdb.client.close()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# routes
app.include_router(code.router, prefix="/code", tags=["code"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(websocket.router, prefix="/websocket", tags=["websocket"])
app.include_router(test.router, prefix="/test", tags=["test"])
app.include_router(collection_data.router, prefix="/collection_data", tags=["collection_data"])


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)