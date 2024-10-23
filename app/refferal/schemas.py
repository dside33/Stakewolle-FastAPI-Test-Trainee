from pydantic import BaseModel, Field, EmailStr


class CreateReferralCode(BaseModel):
    exp: int = Field(ge=1, le=3)


class EmailRequest(BaseModel):
    email: EmailStr
