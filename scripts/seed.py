from decimal import Decimal

from sqlalchemy import select

from app.db import SessionLocal, create_tables
from app.models import Product

PRODUCTS = [
    ("P1001", "Wireless Mouse", 50, Decimal("650.00"), Decimal("18.00")),
    ("P1002", "Keyboard", 40, Decimal("1200.00"), Decimal("18.00")),
    ("P1003", "USB-C Cable", 100, Decimal("300.00"), Decimal("12.00")),
    ("P1004", "Laptop Stand", 25, Decimal("1500.00"), Decimal("18.00")),
]

create_tables()
with SessionLocal() as db:
    for product_id, name, stock, price, tax in PRODUCTS:
        if not db.scalar(select(Product).where(Product.product_id == product_id)):
            db.add(Product(product_id=product_id, name=name, available_stock=stock, unit_price=price, tax_percentage=tax))
    db.commit()
print("Seed complete")
