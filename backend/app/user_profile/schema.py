from enum import Enum
from sqlmodel import SQLModel, Field
from datetime import date
from pydantic_extra_types.country import CountryShortName
from pydantic_extra_types.phone_numbers import PhoneNumber

class SalutationSchema(str,Enum):
    Mr = "Mr"
    Mrs = "Mrs"
    Miss = "Miss"

class GenderSchema(str,Enum):
    Male = "Male"
    Female = "Female"
    Other = "Other"
    
class MaritalStatusSchema(str,Enum):
    Married = "Married"
    Divorced = "Divorced"
    Single = "Single"
    Widowed = "Widowed"

class IdentificationTypeSchema(str,Enum):
    Passport = "Passport"
    Drivers_License = "Driver_License"
    National_ID = "National_ID"

class EmploymentStatusSchema(str,Enum):
    Employed = "Employed"
    Unemployed = "Unemployed"
    Self_Employed = "Self_Employed"
    Student = "Student"
    Retired = "Retired"
    
class ProfileBaseSchema(SQLModel, table=False):
    title: SalutationSchema
    gender: GenderSchema
    date_of_birth: date
    country_of_birth: CountryShortName
    place_of_birth: str
    marital_status: MaritalStatusSchema
    means_of_identification: IdentificationTypeSchema
    id_issue_date: date
    id_expiry_date: date
    passport_number: str
    phone_number: PhoneNumber
    nationality: str
    address:str
    city:str
    country:str
    employment_status: EmploymentStatusSchema
    employer_name: str
    employer_address: str
    employer_city: str
    employer_country: str
    annual_income: float
    date_of_employment: date
    profile_photo_url: str | None = Field(default=None)
    id_photo_url: str | None = Field(default=None)
    signature_photo_url: str | None = Field(default=None)
    