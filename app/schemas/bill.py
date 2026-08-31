from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ALLOWED_DENOMINATIONS = (500, 50, 20, 10, 5, 2, 1)


class BillItemRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=50)
    quantity: int = Field(gt=0)


class DenominationRequest(BaseModel):
    value: int
    count: int = Field(ge=0)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: int) -> int:
        if value not in ALLOWED_DENOMINATIONS:
            raise ValueError(f"Unsupported denomination: {value}")
        return value


class BillCreateRequest(BaseModel):
    customer_email: EmailStr
    items: list[BillItemRequest] = Field(min_length=1)
    denominations: list[DenominationRequest] = Field(min_length=1)
    amount_paid: Decimal = Field(ge=0, decimal_places=2)

    @field_validator("items")
    @classmethod
    def no_duplicate_products(cls, items: list[BillItemRequest]) -> list[BillItemRequest]:
        ids = [item.product_id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("A product can only appear once in a bill")
        return items

    @field_validator("denominations")
    @classmethod
    def no_duplicate_denominations(cls, denominations: list[DenominationRequest]) -> list[DenominationRequest]:
        values = [item.value for item in denominations]
        if len(values) != len(set(values)):
            raise ValueError("A denomination can only appear once")
        return denominations


class BillItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str
    product_name: str
    unit_price: Decimal
    quantity: int
    purchase_price: Decimal
    tax_percentage: Decimal
    tax_amount: Decimal
    total_price: Decimal


class DenominationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    value: int
    count: int


class BillResponse(BaseModel):
    id: int
    customer_email: EmailStr
    total_before_tax: Decimal
    total_tax: Decimal
    net_payable: Decimal
    rounded_down_payable: Decimal
    amount_paid: Decimal
    change_due: Decimal
    created_at: datetime
    items: list[BillItemResponse]
    denominations: list[DenominationResponse]
    change_denominations: dict[int, int]
