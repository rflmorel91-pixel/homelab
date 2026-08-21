import os
import smtplib
from email.message import EmailMessage

from app.products.renewaldesk.models import (
    RenewalItem,
    RenewalReminderDelivery,
)


def smtp_config() -> dict[str, object]:
    host = os.getenv("RENEWALDESK_SMTP_HOST")
    port = int(
        os.getenv(
            "RENEWALDESK_SMTP_PORT",
            "587",
        )
    )
    username = os.getenv(
        "RENEWALDESK_SMTP_USERNAME"
    )
    password = os.getenv(
        "RENEWALDESK_SMTP_PASSWORD"
    )
    from_email = os.getenv(
        "RENEWALDESK_SMTP_FROM_EMAIL"
    )
    use_tls = (
        os.getenv(
            "RENEWALDESK_SMTP_USE_TLS",
            "true",
        ).lower()
        in {"1", "true", "yes", "on"}
    )

    if not host:
        raise RuntimeError(
            "RENEWALDESK_SMTP_HOST is required"
        )

    if not from_email:
        raise RuntimeError(
            "RENEWALDESK_SMTP_FROM_EMAIL is required"
        )

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_email": from_email,
        "use_tls": use_tls,
    }


def build_reminder_message(
    item: RenewalItem,
) -> EmailMessage:
    if not item.owner_email:
        raise RuntimeError(
            "Renewal item has no owner email"
        )

    message = EmailMessage()

    config = smtp_config()

    message["From"] = str(
        config["from_email"]
    )
    message["To"] = item.owner_email
    message["Subject"] = (
        f"Renewal reminder: {item.name}"
    )

    message.set_content(
        "\n".join(
            [
                f"Renewal: {item.name}",
                (
                    "Renewal date: "
                    f"{item.renewal_date.isoformat()}"
                ),
                (
                    "Responsible owner: "
                    f"{item.owner_name or 'Not assigned'}"
                ),
                "",
                (
                    "This reminder was generated "
                    "by RenewalDesk."
                ),
            ]
        )
    )

    return message


def send_reminder_email(
    delivery: RenewalReminderDelivery,
    item: RenewalItem,
) -> None:
    if delivery.channel != "email":
        raise RuntimeError(
            "Unsupported reminder channel"
        )

    config = smtp_config()
    message = build_reminder_message(item)

    with smtplib.SMTP(
        str(config["host"]),
        int(config["port"]),
        timeout=15,
    ) as smtp:
        if config["use_tls"]:
            smtp.starttls()

        username = config["username"]
        password = config["password"]

        if username:
            if not password:
                raise RuntimeError(
                    "SMTP password is required "
                    "when username is configured"
                )

            smtp.login(
                str(username),
                str(password),
            )

        smtp.send_message(message)
