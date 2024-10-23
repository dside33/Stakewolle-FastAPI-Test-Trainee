from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserCreate, UserLogin, Token, UserOut
from .logic import register_user_logic, login_user_logic

from app.core.database import get_async_session


auth_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


@auth_router.post("/register", response_model=UserOut)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_async_session)):
    return await register_user_logic(user_in, db)


@auth_router.post("/login", response_model=Token)
async def login_for_access_token(response: Response, user_in: UserLogin, db: AsyncSession = Depends(get_async_session)):
    return await login_user_logic(response, user_in, db)
