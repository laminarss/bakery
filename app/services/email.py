from email.message import EmailMessage
import smtplib

from app.config import get_settings
from app.models import Bill


def render_invoice_text(bill: Bill) -> str:
    lines = [
        f"Invoice #{bill.id}",
        f"Customer: {bill.customer_email}",
        "",
        "Items:",
    ]
    for item in bill.items:
        lines.append(
            f"- {item.product_name} ({item.product_id}) x {item.quantity}: "
            f"₹{item.total_price:.2f}"
        )
    lines += [
        "",
        f"Subtotal: ₹{bill.total_before_tax:.2f}",
        f"Tax: ₹{bill.total_tax:.2f}",
        f"Total: ₹{bill.net_payable:.2f}",
        f"Paid: ₹{bill.amount_paid:.2f}",
        f"Change: ₹{bill.change_due:.2f}",
    ]
    return "\n".join(lines)


def send_invoice_email(bill: Bill) -> None:
    settings = get_settings()
    if not settings.email_enabled:
        return

    message = EmailMessage()
    message["Subject"] = f"Invoice #{bill.id}"
    message["From"] = settings.smtp_from
    message["To"] = bill.customer_email
    message.set_content(render_invoice_text(bill))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_username:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)
