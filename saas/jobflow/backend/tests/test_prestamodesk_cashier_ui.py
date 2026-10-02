import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPOSITORY_ROOT / "app"
CASHIER_PAGE = APP_ROOT / "prestamodesk-caja.html"
PRODUCTION_NGINX = (
    REPOSITORY_ROOT / "nginx" / "default.conf"
)
STAGING_NGINX = (
    REPOSITORY_ROOT / "staging" / "nginx.conf"
)


def cashier_script_path() -> Path:
    contents = CASHIER_PAGE.read_text()
    match = re.search(
        r'src="(/assets/prestamodesk-caja-'
        r'[0-9a-f]{12}\.js)"',
        contents,
    )
    assert match is not None
    return APP_ROOT / match.group(1).removeprefix("/")


def test_cashier_page_references_fingerprinted_asset():
    assert CASHIER_PAGE.is_file()

    script = cashier_script_path()

    assert script.is_file()
    assert (
        "/assets/prestamodesk-caja.js"
        not in CASHIER_PAGE.read_text()
    )


def test_cashier_page_avoids_inline_code():
    contents = CASHIER_PAGE.read_text()

    assert not re.search(
        r"<script(?![^>]*\bsrc=)",
        contents,
    )
    assert not re.search(r"\sstyle=", contents)
    assert not re.search(
        r"\son(?:click|change|submit)=",
        contents,
    )


def test_cashier_page_has_separate_payment_workflow():
    html = CASHIER_PAGE.read_text()
    script = cashier_script_path().read_text()

    for element_id in (
        "cashierWorkspace",
        "loanSearchForm",
        "loanSearchQuery",
        "cashierLoanList",
        "loanDetailPanel",
        "paymentForm",
        "paymentInstallment",
        "paymentAmount",
        "paymentDate",
        "paymentMethod",
        "paymentReference",
        "receiptPanel",
        "receiptContent",
    ):
        assert f'id="{element_id}"' in html

    for expected in (
        "/cashier/loans",
        "/payments",
        "borrower_full_name",
        "borrower_document_number",
        "ordinary_balance_due",
        "late_fee_balance_due",
        "balance_due",
        "ordinary_balance",
        "late_fee_balance",
        "total_balance",
        "installments",
        "as_of",
        "paid_at",
        "late_fee_amount",
        "interest_amount",
        "principal_amount",
        "installment_ordinary_balance",
        "installment_late_fee_balance",
        "receipt_number",
        "Imprimir recibo",
    ):
        assert expected in html + script

    for forbidden in (
        "/applications",
        "/prospects",
        "/borrowers",
        "Nuevo prestatario",
        "Crear préstamo",
    ):
        assert forbidden not in html + script


def test_nginx_serves_cashier_with_enforced_csp():
    production = PRODUCTION_NGINX.read_text()
    staging = STAGING_NGINX.read_text()

    for contents in (production, staging):
        assert (
            "location = /prestamodesk/caja {"
            in contents
        )
        assert (
            "try_files /prestamodesk-caja.html =404;"
            in contents
        )

    assert (
        r"prestamodesk(?:-(?:app|caja)\.html"
        in production
    )
    assert (
        "/prestamodesk-caja.html "
        "\"default-src 'self';"
        in staging
    )


def test_cashier_page_supports_personal_cash_closing():
    html = CASHIER_PAGE.read_text()
    script = cashier_script_path().read_text()

    for element_id in (
        "cashClosingPanel",
        "cashClosingPreview",
        "cashClosingForm",
        "cashCounted",
        "cashClosingNotes",
        "cashClosingReceipt",
        "cashClosingReceiptContent",
        "printCashClosingButton",
        "cashClosingHistoryPanel",
        "cashClosingHistory",
    ):
        assert f'id="{element_id}"' in html

    for expected in (
        "Cierre de caja",
        "Efectivo contado",
        "Cerrar mi caja",
        "Comprobante de cierre",
        "Mis cierres anteriores",
        "/cashier/closing-preview",
        "/cashier/closings",
        "cash_counted",
        "cash_difference",
        "bank_transfer_total",
        "card_total",
        "other_total",
        "loadCashClosing",
        "Caja cerrada correctamente.",
        'currentRole !== "member"',
    ):
        assert expected in html + script
