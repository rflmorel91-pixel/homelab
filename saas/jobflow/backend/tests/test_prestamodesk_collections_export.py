import csv
import io
from datetime import date

from tests.test_prestamodesk_collections import (
    BASE_URL,
    create_loan,
    create_tenant,
    role_headers,
)


EXPORT_URL = (
    f"{BASE_URL}/collections/supervision/export.csv"
)


def csv_rows(response):
    assert response.content.startswith(
        b"\xef\xbb\xbf"
    )

    return list(
        csv.reader(
            io.StringIO(
                response.content.decode("utf-8-sig")
            )
        )
    )


def test_owner_exports_tenant_overdue_portfolio(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=890,
        slug="collections-export",
    )
    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )

    borrower, loan, _ = create_loan(
        db_session,
        tenant=tenant,
        suffix=890,
        due_date=date(2026, 9, 1),
    )
    borrower.full_name = "=RIESGO CSV"
    borrower.email = "+formula@example.test"

    other_tenant = create_tenant(
        db_session,
        client_number=891,
        slug="collections-export-other",
    )
    create_loan(
        db_session,
        tenant=other_tenant,
        suffix=891,
        due_date=date(2026, 8, 1),
    )
    db_session.commit()

    response = authenticated_client.get(
        EXPORT_URL,
        params={"as_of": "2026-10-02"},
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/csv"
    )
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"] == (
        "attachment; filename="
        '"prestamodesk-cartera-vencida-'
        '2026-10-02.csv"'
    )

    rows = csv_rows(response)

    assert len(rows) == 2
    assert rows[0][0] == "Préstamo"
    assert rows[0][-1] == "Fecha de corte"
    assert rows[1][0] == str(loan.id)
    assert rows[1][1] == "'=RIESGO CSV"
    assert rows[1][4] == "'+formula@example.test"
    assert rows[1][5] == "Sin asignar"
    assert rows[1][6] == "2026-09-01"
    assert rows[1][7] == "31"
    assert rows[1][8] == "1"
    assert rows[1][9] == "1000.00"
    assert rows[1][10] == "0.00"
    assert rows[1][11] == "1000.00"
    assert rows[1][12] == "DOP"
    assert rows[1][13] == "2026-10-02"


def test_collections_export_requires_owner(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=892,
        slug="collections-export-security",
    )
    create_loan(
        db_session,
        tenant=tenant,
        suffix=892,
    )

    for role in ("collector", "member"):
        headers = role_headers(
            authenticated_client,
            db_session,
            tenant,
            role,
        )
        response = authenticated_client.get(
            EXPORT_URL,
            params={"as_of": "2026-10-02"},
            headers=headers,
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Owner role required"
        )


def test_owner_exports_empty_report_with_header(
    authenticated_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        client_number=893,
        slug="collections-export-empty",
    )
    owner_headers = role_headers(
        authenticated_client,
        db_session,
        tenant,
        "owner",
    )

    response = authenticated_client.get(
        EXPORT_URL,
        params={"as_of": "2026-10-02"},
        headers=owner_headers,
    )

    assert response.status_code == 200
    rows = csv_rows(response)
    assert len(rows) == 1
    assert rows[0][0] == "Préstamo"
    assert rows[0][-1] == "Fecha de corte"
