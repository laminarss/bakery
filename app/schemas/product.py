from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    available_stock: int = Field(ge=0)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    tax_percentage: Decimal = Field(ge=0, le=100, decimal_places=2)


class ProductCreate(ProductBase):
    product_id: str = Field(min_length=1, max_length=50)


class ProductUpdate(ProductBase):
    pass


class ProductResponse(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
