from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, func, Integer, ForeignKey

from datetime import datetime

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(primary_key=True)
    name:Mapped[str]
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    reffered_by_code_id: Mapped[int] = mapped_column(Integer, ForeignKey("referral_codes.id"), nullable=True)

    referral_codes = relationship("ReferralCode", back_populates="user", foreign_keys="ReferralCode.user_id")