from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    email: EmailStr


class VerifyTokenSchema(BaseModel):
    email: EmailStr
    token: str


class ResetPasswordSchema(BaseModel):
    email: EmailStr
    token: str
    new_password: str
