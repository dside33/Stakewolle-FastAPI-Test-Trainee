from fastapi import HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from .models import User
from .schemas import UserCreate, UserLogin
from .utils import get_user_from_db, create_jwt_token

from app.refferal.models import ReferralCode
from app.core.cfg import settings


async def register_user_logic(user_in: UserCreate, db: AsyncSession):
    user = await get_user_from_db(user_in, db)

    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    refferal_code_id = None
    if user_in.refferal_code != "":
        result = await db.execute(select(ReferralCode).where(ReferralCode.code==user_in.refferal_code))
        refferal_code_id = (result.scalar_one_or_none()).id

        if refferal_code_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral code not found")

    new_user = User(
                    name=user_in.name,
                    email=user_in.email,
                    password=user_in.password,
                    reffered_by_code_id=refferal_code_id
                    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def login_user_logic(response: Response, user_in: UserLogin, db: AsyncSession):
    user = await get_user_from_db(user_in, db)

    if not user or user.password != user_in.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = {
        "sub": user.email,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iss": settings.ISSUER
    }

    access_token = create_jwt_token(user_data)
    response.headers["Authorization"] = f"Bearer {access_token}"

    return {"access_token": access_token, "token_type": "bearer"}
