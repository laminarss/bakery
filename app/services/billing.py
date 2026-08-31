from collections import Counter
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Bill, BillDenomination, BillItem, Product
from app.schemas.bill import BillCreateRequest

MONEY = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_change(amount: int, denominations: dict[int, int]) -> dict[int, int] | None:
    """Return an exact change combination using limited available notes/coins.

    Bounded subset-sum dynamic programming guarantees that an exact combination is
    found when one exists, unlike a greedy algorithm which can fail with limited stock.
    """
    if amount == 0:
        return {}

    reachable: dict[int, tuple[int, ...]] = {0: ()}
    for value in sorted(denominations, reverse=True):
        count = denominations[value]
        for _ in range(count):
            snapshot = list(reachable.items())
            for total, used in snapshot:
                new_total = total + value
                if new_total <= amount and new_total not in reachable:
                    reachable[new_total] = used + (value,)
                    if new_total == amount:
                        return dict(Counter(reachable[new_total]))
    return None


def create_bill(db: Session, request: BillCreateRequest) -> Bill:
    product_ids = [item.product_id for item in request.items]
    products = db.scalars(
        select(Product).where(Product.product_id.in_(product_ids)).with_for_update()
    ).all()
    product_map = {product.product_id: product for product in products}

    missing = [product_id for product_id in product_ids if product_id not in product_map]
    if missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Products not found: {', '.join(missing)}")

    total_before_tax = Decimal("0")
    total_tax = Decimal("0")
    calculated_items: list[dict] = []

    for requested in request.items:
        product = product_map[requested.product_id]
        if requested.quantity > product.available_stock:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for product {product.product_id}",
            )

        purchase_price = money(product.unit_price * requested.quantity)
        tax_amount = money(purchase_price * product.tax_percentage / Decimal("100"))
        total_price = money(purchase_price + tax_amount)
        total_before_tax += purchase_price
        total_tax += tax_amount
        calculated_items.append(
            {
                "product": product,
                "quantity": requested.quantity,
                "purchase_price": purchase_price,
                "tax_amount": tax_amount,
                "total_price": total_price,
            }
        )

    total_before_tax = money(total_before_tax)
    total_tax = money(total_tax)
    net_payable = money(total_before_tax + total_tax)
    rounded_down_payable = net_payable.quantize(Decimal("1"), rounding=ROUND_FLOOR).quantize(MONEY)

    if request.amount_paid < rounded_down_payable:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount paid is less than the rounded bill amount")

    # The supplied reference screen shows the rounded-down payable amount being
    # used to calculate the customer's balance.
    change_due = money(request.amount_paid - rounded_down_payable)

    denomination_map = {item.value: item.count for item in request.denominations}
    change_denominations = calculate_change(int(change_due), denomination_map)
    if change_denominations is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exact change cannot be made with the available denominations",
        )

    bill = Bill(
        customer_email=str(request.customer_email),
        total_before_tax=total_before_tax,
        total_tax=total_tax,
        net_payable=net_payable,
        rounded_down_payable=rounded_down_payable,
        amount_paid=money(request.amount_paid),
        change_due=change_due,
    )
    db.add(bill)

    for item in calculated_items:
        product = item["product"]
        product.available_stock -= item["quantity"]
        bill.items.append(
            BillItem(
                product_id=product.product_id,
                product_name=product.name,
                unit_price=product.unit_price,
                quantity=item["quantity"],
                purchase_price=item["purchase_price"],
                tax_percentage=product.tax_percentage,
                tax_amount=item["tax_amount"],
                total_price=item["total_price"],
            )
        )

    for value, count in sorted(denomination_map.items(), reverse=True):
        bill.denominations.append(BillDenomination(value=value, count=count))

    db.commit()
    db.refresh(bill)
    return bill


def get_bill(db: Session, bill_id: int) -> Bill | None:
    return db.scalar(
        select(Bill)
        .options(selectinload(Bill.items), selectinload(Bill.denominations))
        .where(Bill.id == bill_id)
    )
