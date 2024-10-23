import jwt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from .schemas import UserLogin
from .models import User

from app.core.cfg import settings
from app.core.database import get_async_session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_jwt_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({ "exp": expire })

    return jwt.encode(to_encode, settings.SECRET, algorithm=settings.ALGORITHM)


async def get_user_from_db(user_in: UserLogin, db: AsyncSession):
    if db is None:
        raise HTTPException(status_code=500, detail="Database session could not be obtained")
    
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()

    return user


async def get_user_from_token(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)):
    try:
        payload = jwt.decode(token, 
                            settings.SECRET, 
                            algorithms=[settings.ALGORITHM], 
                            options={"verify_iss": True}, 
                            issuer=settings.ISSUER)
        
        user_email = payload.get("sub")

        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: subject not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        result = await db.execute(select(User).where(User.email == user_email))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.JWTError, jwt.InvalidTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )