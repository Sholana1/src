from enum import Enum
from sqlmodel import SQLModel, Field
from pydantic import EmailStr, field_validator
from fastapi import HTTPException, status  # Correct: uppercase 'HTTP'


class SecurityQuestionSchema(str, Enum):
    MOTHER_MAIDEN_NAME = "mother_maiden_name"
    CHILDHOOD_FRIEND = "childhood_friend"
    FAVORITE_COLOR = "favorite_color"
    BIRTH_CITY = "birth_city"

    @classmethod
    def get_description(cls, value: "SecurityQuestionSchema") -> str:
        descriptions = {
            cls.MOTHER_MAIDEN_NAME: "What is your mother's maiden name?",
            cls.CHILDHOOD_FRIEND: "What is the name of your childhood best friend?",
            cls.FAVORITE_COLOR: "What is your favorite color?",
            cls.BIRTH_CITY: "In which city were you born?",
        }
        return descriptions.get(value, "Unknown security question")

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    
    
class RoleChoiceSchema(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    BRANCH_MANAGER = "branch_manager"
    TELLER = "teller"
    ACCOUNT_EXECUTIVE = "account_executive"
    SUPER_ADMIN = "super_admin"

class BaseUserSchema(SQLModel, table=False):
    username: str | None = Field(default=None, max_length=20, unique=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    first_name: str = Field(max_length=30)
    middle_name: str | None = Field(default=None, max_length=30)
    last_name: str | None = Field(max_length=30)
    id_no: int = Field(unique=True, gt=0)
    is_active: bool = False
    is_superuser: bool = False
    security_question: SecurityQuestionSchema = Field(max_length=30)
    security_answer: str = Field(max_length=30)
    account_status:AccountStatus = Field(default=AccountStatus.INACTIVE)
    role: RoleChoiceSchema = Field(default=RoleChoiceSchema.CUSTOMER)

class UserCreateSchema(BaseUserSchema):
    password: str = Field(min_length=8, max_length=40)
    confirm_password: str = Field(min_length=8, max_length=40)
    
    @field_validator("confirm_password")
    def validate_confirm_password(cls, v, values):
        if "password" in values.data and v != values.data["password"]:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                details = {
                    "status": "error",
                    "message": "Password do not match",
                    "action": "Please ensure that the password you entered match"
                }
            )
        return v
    