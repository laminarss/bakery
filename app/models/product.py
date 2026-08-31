from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    available_stock: Mapped[int] = mapped_column(nullable=False, default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_percentage: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    bill_items: Mapped[list["BillItem"]] = relationship(back_populates="product")
