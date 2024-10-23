from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from pydantic import EmailStr

from datetime import datetime
import uuid
import redis
import json

from app.refferal.models import ReferralCode
from app.auth.models import User


redis_cache = redis.Redis(host='localhost', port=6379, db=0)


async def create_referral_code(user: User, exp_date: datetime, db: AsyncSession):
    result = await db.execute(select(ReferralCode).where(ReferralCode.user_id == user.id))
    existing_code = result.scalar_one_or_none()
    
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active referral code."
        )

    new_code = ReferralCode(
        code=str(uuid.uuid4()),
        expiration=exp_date,
        user_id=user.id
    )
    
    db.add(new_code)
    await db.commit()
    await db.refresh(new_code)

    cached_data = {
        "code": new_code.code,
        "expiration": new_code.expiration.isoformat()
    }
    redis_cache.setex(f"referral_code:{user.id}", 3600, json.dumps(cached_data))

    return new_code


async def delete_referral_code(user: User, db: AsyncSession):
    result = await db.execute(select(ReferralCode).where(ReferralCode.user_id == user.id))
    existing_code = result.scalar_one_or_none()
    
    if not existing_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active referral code found."
        )
    
    await db.delete(existing_code)
    await db.commit()

    return {"message": "Referral code deleted successfully"}


async def get_code_by_email(email: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    cached_data = redis_cache.get(f"referral_code:{user.id}")

    if cached_data:
        data = json.loads(cached_data)
        code = data["code"]
        expiration = datetime.fromisoformat(data["expiration"])
    else:
        result = await db.execute(select(ReferralCode).where(ReferralCode.user_id == user.id))
        referral_code = result.scalar_one_or_none()

        if referral_code is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail="No active referral code found for this user")

        cached_data = {
            "code": referral_code.code,
            "expiration": referral_code.expiration.isoformat()
        }
        redis_cache.setex(f"referral_code:{user.id}", 3600, json.dumps(cached_data))

        code = referral_code.code
        expiration = referral_code.expiration

    return {"referral_code": code, "expiration": expiration}


async def get_referrals_by_email(referrer_email: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == referrer_email))
    referrer = result.scalar_one_or_none()

    if referrer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referrer with this email not found")

    result = await db.execute(select(ReferralCode).where(ReferralCode.user_id == referrer.id))
    referral_code = result.scalar_one_or_none()

    if referral_code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral code not found for this user")

    referrals = await db.execute(select(User).where(User.reffered_by_code_id == referral_code.id))
    referral_users = referrals.scalars().all()

    if not referral_users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found registered with this referral code")

    return [{"id": user.id, "name": user.name, "email": user.email, "registered_at": user.created_at} for user in referral_users]