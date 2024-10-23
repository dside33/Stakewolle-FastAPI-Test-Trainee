from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from .logic import (create_referral_code, 
                    delete_referral_code, 
                    get_code_by_email,
                    get_referrals_by_email)
from .schemas import CreateReferralCode, EmailRequest

from app.auth.models import User
from app.auth.utils import get_user_from_token
from app.core.database import get_async_session

from datetime import datetime, timedelta


refferal_router = APIRouter()


@refferal_router.post("/create")
async def create_code(create_code: CreateReferralCode, user: 
                      User = Depends(get_user_from_token), 
                      db: AsyncSession = Depends(get_async_session)):
    
    expiration_date = datetime.utcnow() + timedelta(days=create_code.exp)
    code = await create_referral_code(user, expiration_date, db)

    return {"referral_code": code, "expiration": code.expiration}   


@refferal_router.delete("/delete")
async def delete_code(user: User = Depends(get_user_from_token), db: AsyncSession = Depends(get_async_session)):
    await delete_referral_code(user, db)

    return {"message": "Referral code deleted"}


@refferal_router.post("/get-code-by-email")
async def get_referral_code_by_email(
                                    email_request: EmailRequest, 
                                    user: User = Depends(get_user_from_token),
                                    db: AsyncSession = Depends(get_async_session)):
    
    return await get_code_by_email(email_request.email, db)


@refferal_router.get("/referrals")
async def get_referrals_by_referrer_id(referrer_email: EmailStr, 
                                       db: AsyncSession = Depends(get_async_session)):

    return await get_referrals_by_email(referrer_email, db)