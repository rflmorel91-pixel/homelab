import os
import smtplib
from email.message import EmailMessage


def _setting(
    platform_name: str,
    renewaldesk_name: str,
    default: str = "",
) -> str:
    return (
        os.getenv(platform_name)
        or os.getenv(renewaldesk_name)
        or default
    )


def smtp_config() -> dict[str, object]:
    host = _setting(
        "PLATFORM_SMTP_HOST",
        "RENEWALDESK_SMTP_HOST",
    )
    port = int(
        _setting(
            "PLATFORM_SMTP_PORT",
            "RENEWALDESK_SMTP_PORT",
            "587",
        )
    )
    username = _setting(
        "PLATFORM_SMTP_USERNAME",
        "RENEWALDESK_SMTP_USERNAME",
    )
    password = _setting(
        "PLATFORM_SMTP_PASSWORD",
        "RENEWALDESK_SMTP_PASSWORD",
    )
    from_email = _setting(
        "PLATFORM_SMTP_FROM_EMAIL",
        "RENEWALDESK_SMTP_FROM_EMAIL",
    )
    use_tls = (
        _setting(
            "PLATFORM_SMTP_USE_TLS",
            "RENEWALDESK_SMTP_USE_TLS",
            "true",
        ).lower()
        in {"1", "true", "yes", "on"}
    )

    if not host:
        raise RuntimeError("Platform SMTP host is required")

    if not from_email:
        raise RuntimeError(
            "Platform SMTP from email is required"
        )

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_email": from_email,
        "use_tls": use_tls,
    }


def send_password_reset_email(
    *,
    to_email: str,
    product_name: str,
    reset_url: str,
) -> None:
    config = smtp_config()

    message = EmailMessage()
    message["From"] = str(config["from_email"])
    message["To"] = to_email
    message["Subject"] = (
        f"Reset your {product_name} password"
    )
    message.set_content(
        "\n".join(
            [
                (
                    f"A password reset was requested "
                    f"for your {product_name} account."
                ),
                "",
                "Use this secure link within 30 minutes:",
                reset_url,
                "",
                (
                    "If you did not request this reset, "
                    "you can ignore this email."
                ),
            ]
        )
    )

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
