from pydantic import BaseModel, EmailStr

class UserPaymentInfo(BaseModel):
    email: EmailStr
    username: str
    phone_number: str
    amount: str