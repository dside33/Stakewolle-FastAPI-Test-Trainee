from fastapi import FastAPI

from app.auth.routes import auth_router
from app.refferal.routes import refferal_router


app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(refferal_router, prefix="/ref")
