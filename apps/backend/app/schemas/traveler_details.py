"""Pydantic schemas for traveler details used in Ancileo Purchase API."""

from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class TravelerDetailsSchema(BaseModel):
    """Schema for individual traveler details.
    
    Used for Ancileo Purchase API insureds array.
    """
    
    id: str = Field(..., description="Unique identifier for the traveler (e.g., '1', '2')")
    title: Literal["Mr", "Ms", "Mrs", "Dr"] = Field(..., description="Title")
    firstName: str = Field(..., min_length=1, description="First name")
    lastName: str = Field(..., min_length=1, description="Last name")
    nationality: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter country code (e.g., 'SG')")
    dateOfBirth: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="Date of birth in YYYY-MM-DD format")
    passport: str = Field(..., min_length=1, description="Passport number")
    email: EmailStr = Field(..., description="Email address")
    phoneType: str = Field(default="mobile", description="Phone type (mobile, home, work)")
    phoneNumber: str = Field(..., min_length=1, description="Phone number")
    relationship: str = Field(default="main", description="Relationship to main traveler (main, spouse, child, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1",
                "title": "Mr",
                "firstName": "John",
                "lastName": "Doe",
                "nationality": "SG",
                "dateOfBirth": "2000-01-01",
                "passport": "E1234567",
                "email": "john.doe@example.com",
                "phoneType": "mobile",
                "phoneNumber": "6581234567",
                "relationship": "main"
            }
        }


class MainContactSchema(TravelerDetailsSchema):
    """Schema for main contact information.
    
    Extends TravelerDetailsSchema with address fields.
    Used for Ancileo Purchase API mainContact object.
    """
    
    address: str = Field(..., min_length=1, description="Street address")
    city: str = Field(..., min_length=1, description="City")
    zipCode: str = Field(..., min_length=1, description="Postal/ZIP code")
    countryCode: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter country code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1",
                "title": "Mr",
                "firstName": "John",
                "lastName": "Doe",
                "nationality": "SG",
                "dateOfBirth": "2000-01-01",
                "passport": "E1234567",
                "email": "john.doe@example.com",
                "phoneType": "mobile",
                "phoneNumber": "6581234567",
                "relationship": "main",
                "address": "123 Orchard Road",
                "city": "Singapore",
                "zipCode": "238858",
                "countryCode": "SG"
            }
        }


class PurchaseRequestSchema(BaseModel):
    """Schema for complete purchase request data."""
    
    insureds: list[TravelerDetailsSchema] = Field(..., min_length=1, description="List of insured travelers")
    mainContact: MainContactSchema = Field(..., description="Main contact information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "insureds": [
                    {
                        "id": "1",
                        "title": "Mr",
                        "firstName": "John",
                        "lastName": "Doe",
                        "nationality": "SG",
                        "dateOfBirth": "2000-01-01",
                        "passport": "E1234567",
                        "email": "john.doe@example.com",
                        "phoneType": "mobile",
                        "phoneNumber": "6581234567",
                        "relationship": "main"
                    }
                ],
                "mainContact": {
                    "id": "1",
                    "title": "Mr",
                    "firstName": "John",
                    "lastName": "Doe",
                    "nationality": "SG",
                    "dateOfBirth": "2000-01-01",
                    "passport": "E1234567",
                    "email": "john.doe@example.com",
                    "phoneType": "mobile",
                    "phoneNumber": "6581234567",
                    "relationship": "main",
                    "address": "123 Orchard Road",
                    "city": "Singapore",
                    "zipCode": "238858",
                    "countryCode": "SG"
                }
            }
        }

