from fastapi import FastAPI, Depends
import contextlib
# from src.database import create_all_tables
from src.api import router


""" 
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    yield
"""


def create_app() -> FastAPI:
    # app_ = FastAPI(lifespan=lifespan)
    app_ = FastAPI()
    app_.include_router(
        router,
    )
    return app_


app = create_app()

