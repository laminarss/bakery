from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Bill
from app.schemas.bill import BillCreateRequest, BillResponse
from app.services.billing import create_bill, get_bill
from app.services.email import send_invoice_email

router = APIRouter(prefix="/api", tags=["Billing"])


def serialize_bill(bill: Bill) -> BillResponse:
    change_denominations: dict[int, int] = {}
    remaining = int(bill.change_due)
    available = {item.value: item.count for item in bill.denominations}
    for value in sorted(available, reverse=True):
        used = min(remaining // value, available[value])
        if used:
            change_denominations[value] = used
            remaining -= used * value
    return BillResponse.model_validate(
        {
            **{field: getattr(bill, field) for field in (
                "id", "customer_email", "total_before_tax", "total_tax", "net_payable",
                "rounded_down_payable", "amount_paid", "change_due", "created_at"
            )},
            "items": bill.items,
            "denominations": bill.denominations,
            "change_denominations": change_denominations,
        }
    )


@router.post("/bills", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
def create_bill_endpoint(
    payload: BillCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    bill = create_bill(db, payload)
    background_tasks.add_task(send_invoice_email, bill)
    return serialize_bill(bill)


@router.get("/bills/{bill_id}", response_model=BillResponse)
def get_bill_endpoint(bill_id: int, db: Session = Depends(get_db)):
    bill = get_bill(db, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return serialize_bill(bill)


@router.get("/purchases", response_model=list[BillResponse])
def purchase_history(
    email: str = Query(min_length=3),
    db: Session = Depends(get_db),
):
    bills = db.scalars(
        select(Bill)
        .options(selectinload(Bill.items), selectinload(Bill.denominations))
        .where(Bill.customer_email == email.strip().lower())
        .order_by(Bill.created_at.desc())
    ).all()
    return [serialize_bill(bill) for bill in bills]
